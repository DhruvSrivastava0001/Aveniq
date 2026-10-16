
package com.churniq.backend.service;

import com.churniq.backend.entity.Customer;
import com.churniq.backend.repository.CustomerRepository;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Service
public class CustomerCsvImportService {

    private final CustomerRepository customerRepository;

    public CustomerCsvImportService(CustomerRepository customerRepository) {
        this.customerRepository = customerRepository;
    }

    @Transactional
    public ImportResult importCustomers(MultipartFile file) throws IOException {

        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException(
                "Please upload a non-empty CSV file."
            );
        }

        if (file.getSize() > 20 * 1024 * 1024) {
            throw new IllegalArgumentException(
                "CSV file must be 20 MB or smaller."
            );
        }

        int imported = 0;
        int skipped = 0;

        List<String> errors = new ArrayList<>();
        Set<String> seenIds = new HashSet<>();

        try (
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(
                    file.getInputStream(),
                    StandardCharsets.UTF_8
                )
            );
            CSVParser parser = CSVFormat.DEFAULT.builder()
                .setHeader()
                .setSkipHeaderRecord(true)
                .setIgnoreEmptyLines(true)
                .get()
                .parse(reader)
        ) {
            Set<String> headers = parser.getHeaderMap().keySet();

            String[] requiredHeaders = {
                "customer_id", "telecom_partner", "gender", "age",
                "state", "city", "pincode", "date_of_registration",
                "num_dependents", "estimated_salary", "calls_made",
                "sms_sent", "data_used", "churn"
            };

            for (String header : requiredHeaders) {
                if (!headers.contains(header)) {
                    throw new IllegalArgumentException(
                        "Missing required CSV column: " + header
                    );
                }
            }

            for (CSVRecord row : parser) {
                try {
                    String customerId = value(row, "customer_id");

                    if (customerId.isBlank()) {
                        throw new IllegalArgumentException(
                            "customer_id is required."
                        );
                    }

                    if (!seenIds.add(customerId)) {
                        throw new IllegalArgumentException(
                            "Duplicate customer_id within this CSV: "
                                + customerId
                        );
                    }

                    if (customerRepository.existsByCustomerId(customerId)) {
                        throw new IllegalArgumentException(
                            "customer_id already exists in the database: "
                                + customerId
                        );
                    }

                    String partner = value(row, "telecom_partner");
                    String gender = value(row, "gender");
                    String state = value(row, "state");
                    String city = value(row, "city");

                    if (partner.isBlank()) {
                        throw new IllegalArgumentException(
                            "telecom_partner is required."
                        );
                    }

                    if (gender.isBlank()) {
                        throw new IllegalArgumentException(
                            "gender is required."
                        );
                    }

                    if (state.isBlank()) {
                        throw new IllegalArgumentException(
                            "state is required."
                        );
                    }

                    if (city.isBlank()) {
                        throw new IllegalArgumentException(
                            "city is required."
                        );
                    }

                    Integer age = integerValue(row, "age");

                    if (age == null || age < 0 || age > 120) {
                        throw new IllegalArgumentException(
                            "age must be between 0 and 120."
                        );
                    }

                    Integer pincode = integerValue(row, "pincode");
                    Integer dependents =
                        integerValue(row, "num_dependents");
                    Double salary =
                        doubleValue(row, "estimated_salary");
                    Integer calls = integerValue(row, "calls_made");
                    Integer sms = integerValue(row, "sms_sent");
                    Double data = doubleValue(row, "data_used");

                    validateNonNegative(pincode, "pincode");
                    validateNonNegative(dependents, "num_dependents");
                    validateNonNegative(salary, "estimated_salary");
                    validateNonNegative(calls, "calls_made");
                    validateNonNegative(sms, "sms_sent");
                    validateNonNegative(data, "data_used");

                    LocalDate registrationDate =
                        dateValue(row, "date_of_registration");

                    Integer churn = integerValue(row, "churn");

                    if (churn == null || (churn != 0 && churn != 1)) {
                        throw new IllegalArgumentException(
                            "churn must be 0 or 1."
                        );
                    }

                    Customer customer = new Customer();
                    customer.setCustomerId(customerId);
                    customer.setTelecomPartner(partner);
                    customer.setGender(gender);
                    customer.setAge(age);
                    customer.setState(state);
                    customer.setCity(city);
                    customer.setPincode(pincode);
                    customer.setDateOfRegistration(registrationDate);
                    customer.setNumDependents(dependents);
                    customer.setEstimatedSalary(salary);
                    customer.setCallsMade(calls);
                    customer.setSmsSent(sms);
                    customer.setDataUsed(data);
                    customer.setTenureMonths(null);

                    customer.setRegistrationYear(
                        registrationDate == null
                            ? null
                            : registrationDate.getYear()
                    );

                    customer.setChurn(churn);

                    customerRepository.save(customer);
                    imported++;

                } catch (RuntimeException ex) {
                    skipped++;

                    String message = ex.getMessage() == null
                        ? "Invalid row."
                        : ex.getMessage();

                    errors.add(
                        "Row " + row.getRecordNumber() + ": " + message
                    );
                }
            }
        }

        return new ImportResult(imported, skipped, errors);
    }

    private String value(CSVRecord row, String column) {
        String result = row.get(column);
        return result == null ? "" : result.trim();
    }

    private Integer integerValue(CSVRecord row, String column) {
        String text = value(row, column);

        if (text.isBlank()) {
            return null;
        }

        try {
            return Integer.valueOf(text);
        } catch (NumberFormatException ex) {
            throw new IllegalArgumentException(
                column + " must be a whole number."
            );
        }
    }

    private Double doubleValue(CSVRecord row, String column) {
        String text = value(row, column);

        if (text.isBlank()) {
            return null;
        }

        try {
            double number = Double.parseDouble(text);

            if (!Double.isFinite(number)) {
                throw new NumberFormatException();
            }

            return number;
        } catch (NumberFormatException ex) {
            throw new IllegalArgumentException(
                column + " must be a valid number."
            );
        }
    }

    private LocalDate dateValue(CSVRecord row, String column) {
        String text = value(row, column);

        if (text.isBlank()) {
            return null;
        }

        try {
            return LocalDate.parse(text);
        } catch (DateTimeParseException ex) {
            throw new IllegalArgumentException(
                column + " must use YYYY-MM-DD format."
            );
        }
    }

    private void validateNonNegative(Number number, String column) {
        if (number != null && number.doubleValue() < 0) {
            throw new IllegalArgumentException(
                column + " cannot be negative."
            );
        }
    }

    public record ImportResult(
        int imported,
        int skipped,
        List<String> errors
    ) {}
}
