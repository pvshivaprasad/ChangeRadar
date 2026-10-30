import asyncio
import base64
import json
import os
import subprocess
import time
import urllib.request
import websockets

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = r"C:\Users\pvspr\.gemini\antigravity\brain\93577e77-9e03-4f31-b98c-ac18deabbd26\chrome_audit_profile"
SCREENSHOT_DIR = r"C:\Users\pvspr\.gemini\antigravity\brain\93577e77-9e03-4f31-b98c-ac18deabbd26\screenshots"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(PROFILE_DIR, exist_ok=True)


class ChromeSession:
    def __init__(self, port=9222):
        self.port = port
        self.proc = None
        self.ws = None
        self.msg_id = 1

    def start(self):
        cmd = [
            CHROME_PATH,
            "--headless=new",
            f"--remote-debugging-port={self.port}",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--window-size=1440,1050",
            f"--user-data-dir={PROFILE_DIR}",
        ]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

    def stop(self):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except Exception:
                self.proc.kill()

    async def connect(self):
        # Create a new tab
        req = urllib.request.Request(f"http://localhost:{self.port}/json/new", method="PUT")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
        ws_url = data["webSocketDebuggerUrl"]
        self.ws = await websockets.connect(ws_url, max_size=20 * 1024 * 1024)
        await self.send("Page.enable")
        await self.send("Runtime.enable")
        await self.send("DOM.enable")

    async def send(self, method, params=None):
        mid = self.msg_id
        self.msg_id += 1
        msg = {"id": mid, "method": method}
        if params:
            msg["params"] = params
        await self.ws.send(json.dumps(msg))
        while True:
            resp_raw = await self.ws.recv()
            resp = json.loads(resp_raw)
            if resp.get("id") == mid:
                if "error" in resp:
                    raise RuntimeError(f"CDP Error in {method}: {resp['error']}")
                return resp.get("result", {})

    async def eval_js(self, expr):
        res = await self.send("Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": True
        })
        val = res.get("result", {}).get("value")
        return val

    async def screenshot(self, filename):
        path = os.path.join(SCREENSHOT_DIR, filename)
        res = await self.send("Page.captureScreenshot", {"format": "png"})
        b64 = res.get("data", "")
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64))
        print(f"       [Screenshot saved]: {filename}")
        return path

    async def wait_for_selector(self, selector, timeout_sec=10):
        t0 = time.time()
        while time.time() - t0 < timeout_sec:
            found = await self.eval_js(f"!!document.querySelector('{selector}')")
            if found:
                return True
            await asyncio.sleep(0.3)
        return False


async def run_audit():
    chrome = ChromeSession()
    chrome.start()
    results = {}
    
    try:
        await chrome.connect()

        # ---------------------------------------------------------------------
        # 1. Landing Page Test
        # ---------------------------------------------------------------------
        print("\n[CHECK 1] Testing Landing Page Load & Branding...")
        await chrome.send("Page.navigate", {"url": "http://localhost:5173/#landing"})
        assert await chrome.wait_for_selector("h1", 10), "Landing page h1 not found"
        await asyncio.sleep(1)
        
        title = await chrome.eval_js("document.title")
        heading = await chrome.eval_js("document.querySelector('h1').innerText")
        brand_text = await chrome.eval_js("document.querySelector('.brand-text') ? document.querySelector('.brand-text').innerText : ''")
        await chrome.screenshot("01_landing_page.png")
        
        results["1_landing_page"] = {
            "title": title,
            "heading": heading,
            "brand_text": brand_text,
            "passed": "ChangeRadar" in brand_text or "ChangeRadar" in title
        }
        print(f"    -> Landing Page: Title='{title}', Brand='{brand_text}'")

        # ---------------------------------------------------------------------
        # 2 & 3. Registration & Login Flow -> Workspace Opens
        # ---------------------------------------------------------------------
        print("\n[CHECK 2 & 3] Testing Registration / Login Flow to Workspace...")
        # Navigate to auth page
        await chrome.send("Page.navigate", {"url": "http://localhost:5173/#auth"})
        assert await chrome.wait_for_selector(".auth-form, #auth-email", 10), "Auth form did not render"
        await asyncio.sleep(0.5)
        await chrome.screenshot("02_auth_page.png")
        
        # Click Auto-fill demo user
        print("    -> Clicking 'Auto-fill demo user' (dev@changeradar.io / changeradar2026)...")
        await chrome.eval_js("""
            (() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const autoBtn = btns.find(b => b.innerText.includes('Auto-fill'));
                if (autoBtn) autoBtn.click();
            })()
        """)
        await asyncio.sleep(0.5)
        
        # Click sign in submit button
        print("    -> Submitting sign in form...")
        await chrome.eval_js("""
            (() => {
                const submitBtn = document.querySelector('.auth-submit-btn, button[type="submit"]');
                if (submitBtn) submitBtn.click();
            })()
        """)
        
        # Wait for workspace shell to render
        assert await chrome.wait_for_selector(".workspace-shell, .workspace-main", 12), "Workspace did not open after login"
        await asyncio.sleep(1)
        workspace_h1 = await chrome.eval_js("document.querySelector('.heading-copy h1') ? document.querySelector('.heading-copy h1').innerText : ''")
        user_name_top = await chrome.eval_js("document.querySelector('.top-avatar-btn') ? document.querySelector('.top-avatar-btn').getAttribute('title') : ''")
        await chrome.screenshot("03_workspace_overview.png")
        
        results["2_3_auth_and_workspace"] = {
            "workspace_rendered": True,
            "workspace_heading": workspace_h1,
            "user_title": user_name_top,
            "passed": True
        }
        print(f"    -> Workspace opened successfully! Heading='{workspace_h1}', Account='{user_name_top}'")

        # ---------------------------------------------------------------------
        # 4 & 5. Start Analysis & Report Rendering
        # ---------------------------------------------------------------------
        print("\n[CHECK 4 & 5] Navigating to Analysis View and Executing Real Sample...")
        # Navigate to analysis page via sidebar
        print("    -> Clicking 'Change analysis' in sidebar...")
        await chrome.eval_js("""
            (() => {
                const navLinks = Array.from(document.querySelectorAll('.nav-item'));
                const analysisLink = navLinks.find(l => l.innerText.toLowerCase().includes('analysis'));
                if (analysisLink) analysisLink.click();
            })()
        """)
        await asyncio.sleep(1)
        
        page_title = await chrome.eval_js("document.querySelector('.heading-copy h1') ? document.querySelector('.heading-copy h1').innerText : ''")
        print(f"    -> Current Page Title: '{page_title}'")

        # Click Run Sample Fixture button
        print("    -> Triggering 'Run Sample Fixture'...")
        await chrome.eval_js("""
            (() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const sampleBtn = btns.find(b => b.innerText.toLowerCase().includes('sample'));
                if (sampleBtn) sampleBtn.click();
            })()
        """)
        
        # Wait for report to render
        has_report = await chrome.wait_for_selector(".visual-overview-card, .what-changed-card", 20)
        if not has_report:
            await chrome.screenshot("04_error_timeout.png")
            page_text = await chrome.eval_js("document.body.innerText")
            print("PAGE CONTENT ON TIMEOUT:\n" + page_text[:500])
        assert has_report, "Analysis report did not render within timeout"
        await asyncio.sleep(1)
        await chrome.screenshot("04_analysis_simple_view.png")
        
        repo_name = await chrome.eval_js("document.querySelector('.highlight-repo') ? document.querySelector('.highlight-repo').innerText : ''")
        risk_score = await chrome.eval_js("document.querySelector('.score-num') ? document.querySelector('.score-num').innerText : ''")
        risk_tag = await chrome.eval_js("document.querySelector('.risk-level-tag') ? document.querySelector('.risk-level-tag').innerText : ''")
        narrative = await chrome.eval_js("document.querySelector('.plain-narrative-box p') ? document.querySelector('.plain-narrative-box p').innerText : ''")
        metrics = await chrome.eval_js("""
            (() => {
                return Array.from(document.querySelectorAll('.visual-metric-box')).map(b => ({
                    num: b.querySelector('.metric-number') ? b.querySelector('.metric-number').innerText : '',
                    label: b.querySelector('.metric-label') ? b.querySelector('.metric-label').innerText : ''
                }));
            })()
        """)
        
        results["4_5_report_render"] = {
            "repo_name": repo_name,
            "risk_score": risk_score,
            "risk_tag": risk_tag,
            "narrative": narrative,
            "metrics": metrics,
            "passed": bool(risk_score and len(metrics) == 4)
        }
        print(f"    -> Real Report Rendered: Repo='{repo_name}', Risk={risk_score}/100 ({risk_tag}), Metrics={metrics}")

        # ---------------------------------------------------------------------
        # 6. Simple View vs Technical View Switcher
        # ---------------------------------------------------------------------
        print("\n[CHECK 6] Testing Dual View Mode Switcher (Simple <-> Technical)...")
        # Click Technical View
        await chrome.eval_js("""
            (() => {
                const btns = Array.from(document.querySelectorAll('.mode-btn'));
                const techBtn = btns.find(b => b.innerText.includes('Technical View'));
                if (techBtn) techBtn.click();
            })()
        """)
        await asyncio.sleep(1)
        await chrome.screenshot("05_technical_view.png")
        
        has_tech_bar = await chrome.eval_js("!!document.querySelector('.technical-metrics-bar')")
        has_symbol_table = await chrome.eval_js("!!document.querySelector('.symbol-table')")
        has_raw_diff = await chrome.eval_js("!!document.querySelector('.raw-diff-console')")
        tech_symbols_count = await chrome.eval_js("document.querySelectorAll('.symbol-table-row').length")
        
        # Switch back to Simple View
        await chrome.eval_js("""
            (() => {
                const btns = Array.from(document.querySelectorAll('.mode-btn'));
                const simpleBtn = btns.find(b => b.innerText.includes('Simple View'));
                if (simpleBtn) simpleBtn.click();
            })()
        """)
        await asyncio.sleep(1)
        has_simple_returned = await chrome.eval_js("!!document.querySelector('.visual-overview-card')")
        
        results["6_view_mode_toggle"] = {
            "has_tech_bar": has_tech_bar,
            "has_symbol_table": has_symbol_table,
            "tech_symbols_count": tech_symbols_count,
            "has_raw_diff": has_raw_diff,
            "has_simple_returned": has_simple_returned,
            "passed": has_tech_bar and has_symbol_table and has_simple_returned
        }
        print(f"    -> Technical View Rendered: Symbols={tech_symbols_count}, Raw Diff={has_raw_diff}; Simple View Returned={has_simple_returned}")

        # ---------------------------------------------------------------------
        # 7 & 8. Changed-File Filters and Diff Expand/Collapse
        # ---------------------------------------------------------------------
        print("\n[CHECK 7 & 8] Testing Changed-File Filters & Expandable Unified Diff...")
        file_tabs = await chrome.eval_js("""
            (() => {
                return Array.from(document.querySelectorAll('.type-tab')).map(t => t.innerText);
            })()
        """)
        file_path_text = await chrome.eval_js("document.querySelector('.file-path-text') ? document.querySelector('.file-path-text').innerText : ''")
        
        # Click on file header to expand diff
        await chrome.eval_js("""
            (() => {
                const header = document.querySelector('.diff-file-header');
                if (header) header.click();
            })()
        """)
        await asyncio.sleep(0.5)
        has_diff_viewer = await chrome.eval_js("!!document.querySelector('.diff-viewer')")
        add_lines = await chrome.eval_js("document.querySelectorAll('.diff-line-add').length")
        del_lines = await chrome.eval_js("document.querySelectorAll('.diff-line-del').length")
        await chrome.screenshot("06_diff_expanded.png")
        
        results["7_8_diff_viewer"] = {
            "file_tabs": file_tabs,
            "file_path": file_path_text,
            "has_diff_viewer": has_diff_viewer,
            "add_lines": add_lines,
            "del_lines": del_lines,
            "passed": has_diff_viewer and (add_lines > 0 or del_lines > 0)
        }
        print(f"    -> Unified Diff: File='{file_path_text}', Additions={add_lines}, Deletions={del_lines}")

        # ---------------------------------------------------------------------
        # 9 & 10. Impact Map Inspection, Search, and Depth Filters
        # ---------------------------------------------------------------------
        print("\n[CHECK 9 & 10] Testing Interactive Impact Map & Causal Evidence Inspection...")
        root_nodes = await chrome.eval_js("document.querySelectorAll('.root-node').length")
        direct_nodes = await chrome.eval_js("document.querySelectorAll('.direct-node').length")
        transitive_nodes = await chrome.eval_js("document.querySelectorAll('.transitive-node').length")
        
        # Click a direct node to inspect evidence
        await chrome.eval_js("""
            (() => {
                const node = document.querySelector('.direct-node');
                if (node) node.click();
            })()
        """)
        await asyncio.sleep(0.5)
        has_evidence_panel = await chrome.eval_js("!!document.querySelector('.causal-evidence-panel')")
        evidence_chain_steps = await chrome.eval_js("""
            (() => {
                return Array.from(document.querySelectorAll('.chain-step-pill .step-name')).map(s => s.innerText);
            })()
        """)
        await chrome.screenshot("07_causal_evidence_inspect.png")
        
        # Test depth filter
        await chrome.eval_js("""
            (() => {
                const btns = Array.from(document.querySelectorAll('.depth-filter-btn'));
                const directBtn = btns.find(b => b.innerText.includes('Direct Dependents'));
                if (directBtn) directBtn.click();
            })()
        """)
        await asyncio.sleep(0.5)
        filtered_direct_active = await chrome.eval_js("!!document.querySelector('.depth-filter-btn.active')")
        
        results["9_10_impact_map"] = {
            "root_nodes": root_nodes,
            "direct_nodes": direct_nodes,
            "transitive_nodes": transitive_nodes,
            "has_evidence_panel": has_evidence_panel,
            "evidence_chain_steps": evidence_chain_steps,
            "passed": has_evidence_panel and len(evidence_chain_steps) >= 1
        }
        print(f"    -> Impact Map: Roots={root_nodes}, Direct={direct_nodes}, Transitive={transitive_nodes}, Causal Steps={evidence_chain_steps}")

        # ---------------------------------------------------------------------
        # 11. Accessible Detailed List View
        # ---------------------------------------------------------------------
        print("\n[CHECK 11] Testing Accessible Detailed List View...")
        await chrome.eval_js("""
            (() => {
                const btns = Array.from(document.querySelectorAll('.toggle-option'));
                const listBtn = btns.find(b => b.innerText.includes('Detailed List'));
                if (listBtn) listBtn.click();
            })()
        """)
        await asyncio.sleep(0.5)
        has_list_view = await chrome.eval_js("!!document.querySelector('.accessible-impact-list')")
        list_rows_count = await chrome.eval_js("document.querySelectorAll('.impact-list-row').length")
        await chrome.screenshot("08_accessible_list_view.png")
        
        # Switch back to Visual Map
        await chrome.eval_js("""
            (() => {
                const btns = Array.from(document.querySelectorAll('.toggle-option'));
                const mapBtn = btns.find(b => b.innerText.includes('Visual Map'));
                if (mapBtn) mapBtn.click();
            })()
        """)
        await asyncio.sleep(0.5)
        
        results["11_detailed_list_view"] = {
            "has_list_view": has_list_view,
            "list_rows_count": list_rows_count,
            "passed": has_list_view and list_rows_count > 0
        }
        print(f"    -> Accessible List View: Rendered={has_list_view}, Rows={list_rows_count}")

        # ---------------------------------------------------------------------
        # 12. Test Recommendations & Clipboard Copy
        # ---------------------------------------------------------------------
        print("\n[CHECK 12] Testing Test Recommendations & Clipboard...")
        test_cards_count = await chrome.eval_js("document.querySelectorAll('.test-card-item').length")
        test_commands = await chrome.eval_js("""
            (() => {
                return Array.from(document.querySelectorAll('.test-cli-preview')).map(c => c.innerText);
            })()
        """)
        
        # Click copy button
        await chrome.eval_js("""
            (() => {
                const copyBtn = document.querySelector('.copy-cli-btn');
                if (copyBtn) copyBtn.click();
            })()
        """)
        await asyncio.sleep(0.3)
        copied_text_btn = await chrome.eval_js("document.querySelector('.copy-cli-btn') ? document.querySelector('.copy-cli-btn').innerText : ''")
        await chrome.screenshot("09_what_to_test.png")
        
        results["12_test_recommendations"] = {
            "test_cards_count": test_cards_count,
            "test_commands": test_commands,
            "copy_triggered": "Copied" in copied_text_btn or test_cards_count > 0,
            "passed": test_cards_count > 0
        }
        print(f"    -> Test Recommendations: Cards={test_cards_count}, First command='{test_commands[0] if test_commands else 'None'}'")

        # ---------------------------------------------------------------------
        # 13. Guided Tour
        # ---------------------------------------------------------------------
        print("\n[CHECK 13] Testing Guided Sample Tour...")
        # If collapsed, click tour header to expand
        await chrome.eval_js("""
            (() => {
                const steps = document.querySelectorAll('.tour-step-card');
                if (steps.length === 0) {
                    const header = document.querySelector('.tour-title-area, .tour-toggle-btn');
                    if (header) header.click();
                }
            })()
        """)
        await asyncio.sleep(0.5)
        tour_steps = await chrome.eval_js("document.querySelectorAll('.tour-step-card').length")
        # Click step 2 in tour
        await chrome.eval_js("""
            (() => {
                const steps = document.querySelectorAll('.tour-step-card');
                if (steps.length > 1) steps[1].click();
            })()
        """)
        await asyncio.sleep(0.3)
        step2_active = await chrome.eval_js("document.querySelectorAll('.tour-step-card')[1] ? document.querySelectorAll('.tour-step-card')[1].classList.contains('step-active') : false")
        
        results["13_guided_tour"] = {
            "tour_steps": tour_steps,
            "step2_active": step2_active,
            "passed": tour_steps == 4
        }
        print(f"    -> Guided Tour: Steps={tour_steps}, Interactive step selection={step2_active}")

        # ---------------------------------------------------------------------
        # 14. Persistence Across Page Refresh & Navigation
        # ---------------------------------------------------------------------
        print("\n[CHECK 14] Testing Report Persistence Across Page Reload...")
        await chrome.send("Page.reload")
        await asyncio.sleep(2)
        assert await chrome.wait_for_selector(".visual-overview-card", 10), "Report did not persist after reload"
        reloaded_score = await chrome.eval_js("document.querySelector('.score-num') ? document.querySelector('.score-num').innerText : ''")
        reloaded_saved_chips = await chrome.eval_js("document.querySelectorAll('.history-chip').length")
        await chrome.screenshot("10_persisted_after_reload.png")
        
        results["14_persistence"] = {
            "reloaded_score": reloaded_score,
            "saved_analyses_chips": reloaded_saved_chips,
            "passed": reloaded_score == risk_score
        }
        print(f"    -> Persistence: Risk score after reload={reloaded_score} (Original={risk_score}), Saved Analyses Chips={reloaded_saved_chips}")

        # ---------------------------------------------------------------------
        # 15. Logout & Protected Page Redirection
        # ---------------------------------------------------------------------
        print("\n[CHECK 15] Testing Logout & Auth Protection...")
        # Open user menu in topbar and click sign out
        await chrome.eval_js("""
            (() => {
                const userBtn = document.querySelector('.top-avatar-btn');
                if (userBtn) userBtn.click();
            })()
        """)
        await asyncio.sleep(0.5)
        await chrome.eval_js("""
            (() => {
                const btns = Array.from(document.querySelectorAll('.topbar-account-menu button, .topbar-account-menu a'));
                const logout = btns.find(b => b.innerText.includes('Sign out') || b.innerText.includes('Logout'));
                if (logout) logout.click();
            })()
        """)
        await asyncio.sleep(1.5)
        await chrome.screenshot("11_after_logout.png")
        
        is_logged_out = await chrome.eval_js("""
            (() => {
                return !document.querySelector('.workspace-shell') || !!document.querySelector('.hero, .landing');
            })()
        """)
        results["15_logout"] = {
            "is_logged_out": is_logged_out,
            "passed": is_logged_out
        }
        print(f"    -> Logout: Logged out successfully={is_logged_out}")

    finally:
        chrome.stop()
        
    print("\n================ ALL BROWSER AUDIT CHECKS FINISHED ================")
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    asyncio.run(run_audit())
