package ai.hhrdr.chainflow.engine.config;

import org.camunda.bpm.engine.IdentityService;
import org.camunda.bpm.engine.ProcessEngine;
import org.camunda.bpm.engine.identity.Group;
import org.camunda.bpm.engine.identity.GroupQuery;
import org.camunda.bpm.engine.identity.User;
import org.camunda.bpm.engine.identity.UserQuery;
import org.camunda.bpm.engine.rest.security.auth.AuthenticationResult;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import javax.servlet.http.HttpServletRequest;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class JwtAuthenticationFilterTest {
    private JwtConfig jwtConfig;
    private JwtAuthenticationFilter filter;
    private ProcessEngine engine;
    private IdentityService identityService;
    private HttpServletRequest request;

    @BeforeEach
    void setUp() {
        String testSecret = java.util.Base64.getEncoder().encodeToString("supersecretkeysupersecretkey123456".getBytes());
        jwtConfig = new JwtConfig(testSecret, 3600_000, "HS256");
        filter = new JwtAuthenticationFilter(jwtConfig);
        engine = mock(ProcessEngine.class);
        identityService = mock(IdentityService.class);
        when(engine.getIdentityService()).thenReturn(identityService);
        request = mock(HttpServletRequest.class);
    }

    @Test
    void testExtractAuthenticatedUserWithValidJWT() {
        String token = jwtConfig.generateToken("user1", "user1@example.com", true, false, true);
        when(request.getHeader("Authorization")).thenReturn("Bearer " + token);

        UserQuery userQuery = mock(UserQuery.class);
        when(identityService.createUserQuery()).thenReturn(userQuery);
        when(userQuery.userId(anyString())).thenReturn(userQuery);
        when(userQuery.singleResult()).thenReturn(null);
        when(identityService.newUser("user1")).thenReturn(new DummyUser("user1"));

        GroupQuery groupQuery = mock(GroupQuery.class);
        when(identityService.createGroupQuery()).thenReturn(groupQuery);
        when(groupQuery.groupId(anyString())).thenReturn(groupQuery);
        when(groupQuery.singleResult()).thenReturn(null);
        when(identityService.newGroup("camunda-admin")).thenReturn(new DummyGroup("camunda-admin"));

        AuthenticationResult result = filter.extractAuthenticatedUser(request, engine);
        assertTrue(result.isAuthenticated());
        assertEquals("user1", result.getAuthenticatedUser());
    }

    @Test
    void testExtractAuthenticatedUserWithInvalidJWT() {
        when(request.getHeader("Authorization")).thenReturn("Bearer invalid.jwt.token");
        AuthenticationResult result = filter.extractAuthenticatedUser(request, engine);
        assertFalse(result.isAuthenticated());
    }

    @Test
    void testUserAutoCreation() {
        String token = jwtConfig.generateToken("newuser", "newuser@example.com", true, false, true);
        when(request.getHeader("Authorization")).thenReturn("Bearer " + token);

        UserQuery userQuery = mock(UserQuery.class);
        when(identityService.createUserQuery()).thenReturn(userQuery);
        when(userQuery.userId(anyString())).thenReturn(userQuery);
        when(userQuery.singleResult()).thenReturn(null);
        when(identityService.newUser("newuser")).thenReturn(new DummyUser("newuser"));

        GroupQuery groupQuery = mock(GroupQuery.class);
        when(identityService.createGroupQuery()).thenReturn(groupQuery);
        when(groupQuery.groupId(anyString())).thenReturn(groupQuery);
        when(groupQuery.singleResult()).thenReturn(null);
        when(identityService.newGroup("camunda-admin")).thenReturn(new DummyGroup("camunda-admin"));

        AuthenticationResult result = filter.extractAuthenticatedUser(request, engine);
        assertTrue(result.isAuthenticated());
        verify(identityService).saveUser(any(User.class));
        verify(identityService).createMembership("newuser", "camunda-admin");
    }

    @Test
    void testExistingUserNoDuplicate() {
        String token = jwtConfig.generateToken("existing", "existing@example.com", true, false, true);
        User existingUser = new DummyUser("existing");
        when(request.getHeader("Authorization")).thenReturn("Bearer " + token);

        UserQuery userQuery = mock(UserQuery.class);
        when(identityService.createUserQuery()).thenReturn(userQuery);
        when(userQuery.userId(anyString())).thenReturn(userQuery);
        when(userQuery.singleResult()).thenReturn(existingUser);

        AuthenticationResult result = filter.extractAuthenticatedUser(request, engine);
        assertTrue(result.isAuthenticated());
        verify(identityService, never()).saveUser(any(User.class));
    }

    // Dummy classes for User/Group objects
    static class DummyUser implements User {
        private String id;
        DummyUser(String id) { this.id = id; }
        @Override public String getId() { return id; }
        @Override public void setId(String id) { this.id = id; }
        @Override public String getFirstName() { return null; }
        @Override public void setFirstName(String s) {}
        @Override public String getLastName() { return null; }
        @Override public void setLastName(String s) {}
        @Override public String getEmail() { return null; }
        @Override public void setEmail(String s) {}
        @Override public String getPassword() { return null; }
        @Override public void setPassword(String s) {}
    }
    static class DummyGroup implements Group {
        private String id;
        DummyGroup(String id) { this.id = id; }
        @Override public String getId() { return id; }
        @Override public void setId(String id) { this.id = id; }
        @Override public String getName() { return null; }
        @Override public void setName(String s) {}
        @Override public String getType() { return null; }
        @Override public void setType(String s) {}
    }
} 