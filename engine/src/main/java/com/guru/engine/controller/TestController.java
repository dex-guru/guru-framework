package com.guru.engine.controller;

import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;

@RestController
@RequestMapping("/test")
public class TestController {

    @GetMapping("/check-file")
    public ResponseEntity<String> checkFile() {
        try {
            Resource resource = new ClassPathResource("static/openapi/openapi.json");
            if (resource.exists()) {
                return ResponseEntity.ok("File exists at: " + resource.getURL().toString());
            } else {
                return ResponseEntity.ok("File does not exist");
            }
        } catch (IOException e) {
            return ResponseEntity.ok("Error checking file: " + e.getMessage());
        }
    }
} 