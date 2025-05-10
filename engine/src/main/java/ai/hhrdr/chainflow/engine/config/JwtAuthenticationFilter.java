package ai.hhrdr.chainflow.engine.config;

import org.camunda.bpm.engine.ProcessEngine;
import org.camunda.bpm.engine.identity.Group;
import org.camunda.bpm.engine.identity.User;
import org.camunda.bpm.engine.rest.security.auth.AuthenticationResult;
import org.camunda.bpm.engine.rest.security.auth.AuthenticationProvider;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class JwtAuthenticationFilter implements AuthenticationProvider {

    private static final Logger LOG = LoggerFactory.getLogger(JwtAuthenticationFilter.class);

    private final JwtConfig jwtConfig;

    // No-arg constructor for Camunda
    public JwtAuthenticationFilter() {
        String secret = System.getenv().getOrDefault("JWT_SECRET", "dGVzdGluZy1kZWZhdWx0LXNlY3JldC1mb3ItanNvbg==");
        long expiration = 86400000L;
        String expirationEnv = System.getenv("JWT_EXPIRATION");
        if (expirationEnv != null) {
            try { expiration = Long.parseLong(expirationEnv); } catch (Exception ignored) {}
        }
        String algorithm = System.getenv().getOrDefault("JWT_ALGORITHM", "HS256");
        this.jwtConfig = new JwtConfig(secret, expiration, algorithm);
    }

    // Constructor for tests or manual injection
    public JwtAuthenticationFilter(JwtConfig jwtConfig) {
        this.jwtConfig = jwtConfig;
    }

    @Override
    public AuthenticationResult extractAuthenticatedUser(HttpServletRequest request, ProcessEngine engine) {
        String token = extractToken(request);

        if (token == null) {
            LOG.warn("JWT token missing in Authorization header");
            return AuthenticationResult.unsuccessful();
        }

        LOG.debug("Received JWT token: {}", token);
        jwtConfig.logRawJwtParts(token);

        if (!jwtConfig.validateToken(token)) {
            LOG.warn("JWT token is invalid or expired: {}", token);
            return AuthenticationResult.unsuccessful();
        }

        String userId = jwtConfig.extractUsername(token);
        String email = jwtConfig.extractEmail(token);
        Boolean isActive = jwtConfig.extractIsActive(token);
        Boolean isSuperuser = jwtConfig.extractIsSuperuser(token);
        Boolean isVerified = jwtConfig.extractIsVerified(token);

        LOG.debug("Extracted from JWT: userId={}, email={}, isActive={}, isSuperuser={}, isVerified={}",
                userId, email, isActive, isSuperuser, isVerified);

        if (userId == null) {
            LOG.error("JWT token missing required claim: sub (userId). Token: {}", token);
            return AuthenticationResult.unsuccessful();
        }
        if (email == null) {
            LOG.error("JWT token missing required claim: email. Token: {}", token);
            return AuthenticationResult.unsuccessful();
        }
        if (isActive == null) {
            LOG.error("JWT token missing required claim: is_active. Token: {}", token);
            return AuthenticationResult.unsuccessful();
        }
        if (isSuperuser == null) {
            LOG.error("JWT token missing required claim: is_superuser. Token: {}", token);
            return AuthenticationResult.unsuccessful();
        }
        if (isVerified == null) {
            LOG.error("JWT token missing required claim: is_verified. Token: {}", token);
            return AuthenticationResult.unsuccessful();
        }

        User user = engine.getIdentityService().createUserQuery()
                .userId(userId)
                .singleResult();

        if (user == null) {
            user = engine.getIdentityService().newUser(userId);
            user.setFirstName(email);
            user.setLastName(email);
            user.setEmail(email);
            engine.getIdentityService().saveUser(user);

            // TODO: Change this to add users to a general user group after it is created.
            // Always add to 'camunda-admin' group for now
            String groupId = "camunda-admin";
            Group group = engine.getIdentityService().createGroupQuery()
                    .groupId(groupId)
                    .singleResult();

            if (group == null) {
                group = engine.getIdentityService().newGroup(groupId);
                group.setName("Camunda Administrators");
                group.setType("WORKFLOW");
                engine.getIdentityService().saveGroup(group);
            }

            engine.getIdentityService().createMembership(userId, groupId);
        }

        return AuthenticationResult.successful(userId);
    }

    @Override
    public void augmentResponseByAuthenticationChallenge(HttpServletResponse response, ProcessEngine engine) {
        response.setHeader("WWW-Authenticate", "Bearer");
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
    }

    private String extractToken(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
} 