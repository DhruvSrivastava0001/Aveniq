
package com.churniq.backend.service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class AnalyticsCacheClient {

    private static final Logger logger =
            LoggerFactory.getLogger(AnalyticsCacheClient.class);

    private static final String INVALIDATE_URL =
            "http://127.0.0.1:8000/internal/cache/invalidate";

    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(2))
            .build();

    public void invalidateCache() {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(INVALIDATE_URL))
                    .timeout(Duration.ofSeconds(3))
                    .POST(HttpRequest.BodyPublishers.noBody())
                    .build();

            HttpResponse<String> response = httpClient.send(
                    request,
                    HttpResponse.BodyHandlers.ofString()
            );

            if (response.statusCode() < 200
                    || response.statusCode() >= 300) {
                logger.warn(
                        "Analytics cache invalidation returned HTTP {}",
                        response.statusCode()
                );
            }

        } catch (Exception ex) {
            // Customer changes should still succeed if analytics is unavailable.
            logger.warn(
                    "Could not invalidate analytics cache: {}",
                    ex.getMessage()
            );
        }
    }
}
