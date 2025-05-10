package ai.hhrdr.chainflow.engine.config;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Date;
import java.util.Base64;

import static org.junit.jupiter.api.Assertions.*;

class JwtConfigTest {
    private static final String TEST_SECRET = Base64.getEncoder().encodeToString("supersecretkeysupersecretkey123456".getBytes());
    private static final long EXPIRATION = 3600_000; // 1 hour in ms
    private static final String ALGORITHM = "HS256";
    private JwtConfig jwtConfig;

    @BeforeEach
    void setUp() {
        jwtConfig = new JwtConfig(TEST_SECRET, EXPIRATION, ALGORITHM);
    }

    @Test
    void testValidTokenSignatureAndClaims() {
        String token = jwtConfig.generateToken("user1", "user1@example.com", true, false, true);
        assertTrue(jwtConfig.validateToken(token));
        assertEquals("user1", jwtConfig.extractUsername(token));
        assertEquals("user1@example.com", jwtConfig.extractEmail(token));
        assertTrue(jwtConfig.extractIsActive(token));
        assertFalse(jwtConfig.extractIsSuperuser(token));
        assertTrue(jwtConfig.extractIsVerified(token));
    }

    @Test
    void testInvalidSignature() {
        String token = jwtConfig.generateToken("user2", "user2@example.com", true, false, true);
        // Tamper with the token
        String tampered = token.substring(0, token.length() - 2) + "ab";
        assertFalse(jwtConfig.validateToken(tampered));
    }

    @Test
    void testExpiredToken() {
        // Create a token that expired 1 hour ago
        Date now = new Date();
        String expiredToken = Jwts.builder()
                .setSubject("user3")
                .claim("email", "user3@example.com")
                .claim("isActive", true)
                .claim("isSuperuser", false)
                .claim("isVerified", true)
                .setIssuedAt(new Date(now.getTime() - 7200_000))
                .setExpiration(new Date(now.getTime() - 3600_000))
                .signWith(jwtConfig.getKey(), SignatureAlgorithm.valueOf(ALGORITHM))
                .compact();
        assertFalse(jwtConfig.validateToken(expiredToken));
    }

    @Test
    void testClaimExtraction() {
        String token = jwtConfig.generateToken("user4", "user4@example.com", false, true, false);
        assertEquals("user4", jwtConfig.extractUsername(token));
        assertEquals("user4@example.com", jwtConfig.extractEmail(token));
        assertFalse(jwtConfig.extractIsActive(token));
        assertTrue(jwtConfig.extractIsSuperuser(token));
        assertFalse(jwtConfig.extractIsVerified(token));
    }
} 