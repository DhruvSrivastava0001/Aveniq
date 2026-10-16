
package com.churniq.backend.controller;

import com.churniq.backend.service.AnalyticsCacheClient;
import com.churniq.backend.service.CustomerCsvImportService;
import com.churniq.backend.service.CustomerCsvImportService.ImportResult;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/customers")
@CrossOrigin(origins = {
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175"
})
public class CustomerImportController {

    private final CustomerCsvImportService csvImportService;
    private final AnalyticsCacheClient analyticsCacheClient;

    public CustomerImportController(
            CustomerCsvImportService csvImportService,
            AnalyticsCacheClient analyticsCacheClient) {
        this.csvImportService = csvImportService;
        this.analyticsCacheClient = analyticsCacheClient;
    }

    @PostMapping(
            value = "/import",
            consumes = MediaType.MULTIPART_FORM_DATA_VALUE
    )
    public ResponseEntity<?> importCustomers(
            @RequestParam("file") MultipartFile file) {

        try {
            ImportResult result = csvImportService.importCustomers(file);

            if (result.imported() > 0) {
                analyticsCacheClient.invalidateCache();
            }

            return ResponseEntity.ok(result);

        } catch (IllegalArgumentException ex) {
            return ResponseEntity.badRequest()
                    .body(new ErrorResponse(ex.getMessage()));

        } catch (Exception ex) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ErrorResponse(
                            "CSV import failed. Check the backend logs."
                    ));
        }
    }

    public record ErrorResponse(String message) {}
}
