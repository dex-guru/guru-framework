package ai.hhrdr.chainflow.engine.config;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import java.security.Key;
import java.util.Base64;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;

@Component
public class JwtConfig {

    private static final Logger LOG = LoggerFactory.getLogger(JwtConfig.class);

    @Value("${jwt.secret:dGVzdGluZy1kZWZhdWx0LXNlY3JldC1mb3ItanNvbg==}")
    private String secret;

    @Value("${jwt.expiration:86400000}")
    private long expiration;

    @Value("${jwt.algorithm:HS256}")
    private String algorithm;

    private Key key;

    // No-arg constructor for Spring
    public JwtConfig() {
        // Do not call initializeKey() here!
    }

    // Constructor for manual instantiation
    public JwtConfig(String secret, long expiration, String algorithm) {
        this.secret = secret;
        this.expiration = expiration;
        this.algorithm = algorithm;
        initializeKey();
    }

    @PostConstruct
    public void postConstruct() {
        initializeKey();
    }

    private void initializeKey() {
        byte[] decodedKey = Base64.getDecoder().decode(secret);
        if (decodedKey.length < 32) {
            this.key = Keys.secretKeyFor(SignatureAlgorithm.valueOf(algorithm));
        } else {
            this.key = Keys.hmacShaKeyFor(decodedKey);
        }
    }

    private static String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }

    public String generateToken(String userId, String email, boolean isActive, boolean isSuperuser, boolean isVerified) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("email", email);
        claims.put("isActive", isActive);
        claims.put("isSuperuser", isSuperuser);
        claims.put("isVerified", isVerified);
        return createToken(claims, userId);
    }

    private String createToken(Map<String, Object> claims, String subject) {
        Date now = new Date();
        return Jwts.builder()
                .setClaims(claims)
                .setSubject(subject)
                .setIssuedAt(now)
                .setExpiration(new Date(now.getTime() + expiration))
                .signWith(key, SignatureAlgorithm.valueOf(algorithm))
                .compact();
    }

    public Boolean validateToken(String token) {
        try {
            return !isTokenExpired(token);
        } catch (Exception e) {
            LOG.error("Exception during JWT validation: {}", e.getMessage(), e);
            return false;
        }
    }

    public String extractUsername(String token) {
        return extractClaim(token, Claims::getSubject);
    }

    public String extractEmail(String token) {
        Claims claims = extractAllClaims(token);
        if (claims == null) {
            LOG.error("extractEmail: claims is null for token: {}", token);
            return null;
        }
        LOG.debug("JWT Claims: {}", claims);
        Object value = claims.get("email");
        return value != null ? value.toString() : null;
    }

    public Boolean extractIsActive(String token) {
        Claims claims = extractAllClaims(token);
        if (claims == null) {
            LOG.error("extractIsActive: claims is null for token: {}", token);
            return null;
        }
        LOG.debug("JWT Claims: {}", claims);
        Object value = claims.get("isActive");
        return value instanceof Boolean ? (Boolean) value : value != null ? Boolean.valueOf(value.toString()) : null;
    }

    public Boolean extractIsSuperuser(String token) {
        Claims claims = extractAllClaims(token);
        if (claims == null) {
            LOG.error("extractIsSuperuser: claims is null for token: {}", token);
            return null;
        }
        LOG.debug("JWT Claims: {}", claims);
        Object value = claims.get("isSuperuser");
        return value instanceof Boolean ? (Boolean) value : value != null ? Boolean.valueOf(value.toString()) : null;
    }

    public Boolean extractIsVerified(String token) {
        Claims claims = extractAllClaims(token);
        if (claims == null) {
            LOG.error("extractIsVerified: claims is null for token: {}", token);
            return null;
        }
        LOG.debug("JWT Claims: {}", claims);
        Object value = claims.get("isVerified");
        return value instanceof Boolean ? (Boolean) value : value != null ? Boolean.valueOf(value.toString()) : null;
    }

    public Date extractExpiration(String token) {
        try {
            return extractClaim(token, Claims::getExpiration);
        } catch (Exception e) {
            LOG.error("Failed to extract expiration from JWT: {}", e.getMessage(), e);
            return null;
        }
    }

    private <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
        final Claims claims = extractAllClaims(token);
        if (claims == null) {
            LOG.error("extractClaim: claims is null for token: {}", token);
            return null;
        }
        return claimsResolver.apply(claims);
    }

    private Claims extractAllClaims(String token) {
        try {
            return Jwts.parserBuilder()
                    .setSigningKey(key)
                    .build()
                    .parseClaimsJws(token)
                    .getBody();
        } catch (Exception e) {
            LOG.error("Failed to parse JWT claims: {}", e.getMessage(), e);
            return null;
        }
    }

    private Boolean isTokenExpired(String token) {
        Date expiration = extractExpiration(token);
        if (expiration == null) {
            LOG.error("JWT expiration is null, treating as expired. Token: {}", token);
            return true;
        }
        return expiration.before(new Date());
    }

    public void logRawJwtParts(String token) {
        try {
            String[] parts = token.split("\\.");
            if (parts.length == 3) {
                String headerJson = new String(java.util.Base64.getUrlDecoder().decode(parts[0]), java.nio.charset.StandardCharsets.UTF_8);
                String payloadJson = new String(java.util.Base64.getUrlDecoder().decode(parts[1]), java.nio.charset.StandardCharsets.UTF_8);
                LOG.debug("JWT Header: {}", headerJson);
                LOG.debug("JWT Payload: {}", payloadJson);
            } else {
                LOG.warn("JWT does not have 3 parts: {}", token);
            }
        } catch (Exception e) {
            LOG.error("Failed to decode JWT parts: {}", e.getMessage(), e);
        }
    }

    public String getSecret() { return secret; }
    public long getExpiration() { return expiration; }
    public String getAlgorithm() { return algorithm; }
    public Key getKey() { return key; }
} 