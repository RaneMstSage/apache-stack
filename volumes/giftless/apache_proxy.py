"""Apache proxy authenticator - trusts Apache's authentication headers and Git LFS basic auth"""
import base64
import binascii
import logging
import os
from typing import Optional
from flask import Request
from giftless.auth import Authenticator
from giftless.auth.identity import DefaultIdentity

# Set up logging
LOG = logging.getLogger(__name__)

# Wildcard scope for full read/write access
ALL_OBJECTS_RW = ["obj:*/*:*"]  # Simplified: equivalent to ["obj:*/*:read", "obj:*/*:write"]

class ApacheProxyAuthenticator(Authenticator):
    """Accept X-Remote-User from Apache or Basic-Auth (SSH-to-HTTP LFS)"""

    def __call__(self, request: Request) -> Optional[DefaultIdentity]:
        """Called by Giftless to authenticate a request."""
        return self.authenticate(request)

    def authenticate(self, request: Request) -> Optional[DefaultIdentity]:
        """
        Authenticate a request using Apache headers or Git LFS basic auth
        Returns DefaultIdentity object if authentication succeeds, None otherwise
        """
        # Security check: Ensure request comes from Apache
        apache_secret = os.environ.get("APACHE_SECRET")
        if apache_secret:  # Only check if secret is configured
            provided_secret = request.headers.get("X-From-Apache")
            if provided_secret != apache_secret:
                LOG.warning("Request without valid Apache secret header from %s",
                            request.remote_addr)
                return None

        # First check for Apache's LDAP authenticated user
        # Handle both common header formats
        user: Optional[str] = (
                request.headers.get("X-Remote-User")
                or request.headers.get("X_REMOTE_USER")  # Some proxies use underscores
        )

        # If no Apache auth, check for Git LFS basic auth (from SSH git push)
        if not user:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Basic "):
                try:
                    # Decode basic auth
                    encoded_credentials = auth_header[6:]  # Remove 'Basic '
                    decoded = base64.b64decode(encoded_credentials).decode("utf-8")
                    user, _ = decoded.split(":", 1)
                except (binascii.Error, ValueError) as exc:
                    LOG.debug("Bad basic-auth header: %s", exc)
                    user = None

        if user:
            # Strip any whitespace from username
            user = user.strip()
            LOG.info("Giftless authenticated: %s", user)  # INFO level for audit trail
            LOG.debug("Full authentication details for '%s' via %s",
                      user,
                      "Apache" if request.headers.get("X-Remote-User") else "Basic-Auth")

            # Optional: For tighter security, extract org/repo from request
            # org = request.view_args.get("org")
            # repo = request.view_args.get("repo")
            # if org and repo:
            #     scopes = [f"obj:{org}/{repo}:read", f"obj:{org}/{repo}:write"]
            # else:
            #     scopes = ALL_OBJECTS_RW

            return DefaultIdentity(
                id=user,
                name=user,
                email=f"{user}@local",
                scopes=ALL_OBJECTS_RW  # Trust Apache's access control
            )

        # No authentication - return None to allow chain processing
        return None

# Factory function for Giftless
def factory(**options):
    """Factory function called by Giftless configuration"""
    return ApacheProxyAuthenticator(**options)