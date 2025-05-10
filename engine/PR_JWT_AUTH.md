# 🔐 Add/Refine JWT Authentication for GURU Engine

## Overview

This PR implements and documents robust JWT authentication for the GURU Engine, enabling secure, stateless, and interoperable integration with other components of the GURU Framework (such as GURU Flow, the frontend, and additional microservices).

---

## Key Benefits

- **Single Sign-On (SSO) Across GURU Framework:**  
  Users and services authenticated by GURU Flow (or another trusted provider) can seamlessly access the Engine using JWTs, enabling unified identity and access management.

- **Stateless Security:**  
  No session storage is required—user identity and claims are securely encoded in the JWT, which is verified on every request.

- **Automatic User Provisioning:**  
  When a valid JWT is presented, the Engine will automatically create the user (if not present) and assign them to the appropriate group, streamlining onboarding and permissions.

- **Flexible Integration:**  
  Any component (Python, JavaScript, etc.) can interact with the Engine by presenting a valid JWT, making the system language- and platform-agnostic.

- **Fine-Grained Access Control:**  
  JWT claims (such as roles, isActive, isVerified) can be leveraged for advanced authorization scenarios.

- **Centralized Secret Management:**  
  JWT secret, expiration, and algorithm are configurable via environment variables or YAML, ensuring easy rotation and alignment with other GURU services.

---

## Technical Highlights

- JWTs are verified on every API request via the `Authorization: Bearer ...` header.
- The Engine's JWT config is loaded from environment variables or YAML, supporting both Spring and non-Spring instantiation.
- The authentication flow is compatible with tokens issued by GURU Flow (FastAPI) and can be extended to other trusted issuers.

---

**This PR lays the foundation for secure, scalable, and maintainable authentication across the entire GURU ecosystem.** 