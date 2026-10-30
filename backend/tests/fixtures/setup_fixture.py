"""Automated synthetic test repository provisioner for ChangeRadar.

Creates a 2-commit git repository fixture modeling real architectural dependencies
(auth -> checkout/user -> tests) to validate change impact analysis without network calls.
"""
import os
import subprocess

SYNTHETIC_REPO_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURE_PATH = os.path.join(SYNTHETIC_REPO_DIR, "synthetic_repo")


def ensure_synthetic_repo() -> str:
    """Ensures the synthetic git repository fixture is initialized with 2 real commits."""
    git_dir = os.path.join(FIXTURE_PATH, ".git")
    if os.path.isdir(git_dir):
        return FIXTURE_PATH

    os.makedirs(FIXTURE_PATH, exist_ok=True)
    auth_dir = os.path.join(FIXTURE_PATH, "auth")
    checkout_dir = os.path.join(FIXTURE_PATH, "checkout")
    user_dir = os.path.join(FIXTURE_PATH, "user")
    tests_dir = os.path.join(FIXTURE_PATH, "tests")

    for d in (auth_dir, checkout_dir, user_dir, tests_dir):
        os.makedirs(d, exist_ok=True)

    # Base version of auth/service.py
    with open(os.path.join(auth_dir, "service.py"), "w", encoding="utf-8") as f:
        f.write('''import hashlib

def hash_password(password: str) -> str:
    """Computes SHA-256 hash of password string."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

class AuthService:
    """Enterprise authentication and session verification service."""
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def validate_token(self, token: str) -> bool:
        """Validates incoming authentication token string."""
        if not token:
            return False
        return len(token) > 16

    def generate_token(self, user_id: str) -> str:
        """Generates standard token for active session."""
        return hash_password(f"{user_id}:{self.secret_key}")
''')

    # checkout/payment.py
    with open(os.path.join(checkout_dir, "payment.py"), "w", encoding="utf-8") as f:
        f.write('''from auth.service import AuthService

class PaymentGateway:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

def process_payment(amount: float, token: str) -> bool:
    """Processes user payment validating authorization token first."""
    service = AuthService("payment_secret")
    if not service.validate_token(token):
        return False
    return amount > 0.0
''')

    # user/profile.py
    with open(os.path.join(user_dir, "profile.py"), "w", encoding="utf-8") as f:
        f.write('''from auth.service import AuthService

class UserProfileManager:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

def get_user_profile(user_id: str, token: str) -> dict:
    """Fetches user profile details after validating session token."""
    service = AuthService("profile_secret")
    if not service.validate_token(token):
        raise PermissionError("Invalid session token")
    return {"user_id": user_id, "active": True}
''')

    # tests/test_auth.py
    with open(os.path.join(tests_dir, "test_auth.py"), "w", encoding="utf-8") as f:
        f.write('''from auth.service import AuthService, hash_password

def test_validate_token():
    auth = AuthService("secret")
    assert auth.validate_token("token_exceeding_minimum_length_123") is True

def test_hash_password():
    h = hash_password("test_pass")
    assert len(h) == 64
''')

    # tests/test_payment.py
    with open(os.path.join(tests_dir, "test_payment.py"), "w", encoding="utf-8") as f:
        f.write('''from checkout.payment import process_payment

def test_process_payment():
    res = process_payment(100.0, "token_sample_abc_12345")
    assert isinstance(res, bool)
''')

    # tests/test_profile.py
    with open(os.path.join(tests_dir, "test_profile.py"), "w", encoding="utf-8") as f:
        f.write('''from user.profile import get_user_profile

def test_get_user_profile():
    try:
        get_user_profile("u123", "token_test_12345")
    except Exception:
        pass
''')

    # Initialize git repo and make initial commit
    subprocess.run(["git", "init"], cwd=FIXTURE_PATH, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "ChangeRadar Tester"], cwd=FIXTURE_PATH, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "tester@changeradar.dev"], cwd=FIXTURE_PATH, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=FIXTURE_PATH, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat(auth): initial authentication and payment services"], cwd=FIXTURE_PATH, check=True, capture_output=True)

    # Now make change to auth/service.py for second commit
    with open(os.path.join(auth_dir, "service.py"), "w", encoding="utf-8") as f:
        f.write('''import hashlib

def hash_password(password: str) -> str:
    """Computes SHA-256 hash of password string."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

class AuthService:
    """Enterprise authentication and session verification service."""
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def validate_token(self, token: str, require_mfa: bool = True) -> bool:
        """Updated token validator requiring MFA check."""
        if not token or (require_mfa and "mfa" not in token):
            return False
        return len(token) > 20

    def generate_token(self, user_id: str) -> str:
        """Generates standard token for active session."""
        return hash_password(f"{user_id}:{self.secret_key}")
''')

    subprocess.run(["git", "add", "auth/service.py"], cwd=FIXTURE_PATH, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat(auth): add MFA requirement to validate_token"], cwd=FIXTURE_PATH, check=True, capture_output=True)

    return FIXTURE_PATH


if __name__ == "__main__":
    path = ensure_synthetic_repo()
    print(f"Synthetic repo ready at: {path}")
