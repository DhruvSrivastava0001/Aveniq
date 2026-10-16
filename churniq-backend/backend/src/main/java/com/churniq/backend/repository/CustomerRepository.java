
package com.churniq.backend.repository;

import com.churniq.backend.entity.Customer;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface CustomerRepository extends JpaRepository<Customer, Long> {
    boolean existsByCustomerId(String customerId);

    @Query("""
        SELECT c FROM Customer c
        WHERE (
            :search IS NULL OR :search = ''
            OR LOWER(c.customerId) LIKE LOWER(CONCAT('%', :search, '%'))
            OR LOWER(c.telecomPartner) LIKE LOWER(CONCAT('%', :search, '%'))
            OR LOWER(c.city) LIKE LOWER(CONCAT('%', :search, '%'))
            OR LOWER(c.state) LIKE LOWER(CONCAT('%', :search, '%'))
        )
        AND (:churn IS NULL OR c.churn = :churn)
        """)
    Page<Customer> searchCustomers(
        @Param("search") String search,
        @Param("churn") Integer churn,
        Pageable pageable
    );
}
