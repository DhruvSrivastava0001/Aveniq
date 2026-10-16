package com.churniq.backend.service;

import com.churniq.backend.entity.Customer;
import com.churniq.backend.repository.CustomerRepository;

import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

import java.util.List;
import java.util.Optional;

@Service
public class CustomerService {

    private final CustomerRepository customerRepository;

    public CustomerService(CustomerRepository customerRepository) {
        this.customerRepository = customerRepository;
    }
    public Page<Customer> searchCustomers(
        String search,
        Integer churn,
        int page,
        int size) {

    Pageable pageable = PageRequest.of(page, size);

    String searchTerm =
            (search == null || search.isBlank()) ? null : search.trim();

    return customerRepository.searchCustomers(
            searchTerm,
            churn,
            pageable
    );
}








    public Page<Customer> getCustomersPaginated(int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
            return customerRepository.findAll(pageable);
    }

    public List<Customer> getAllCustomers() {
        return customerRepository.findAll();
    }

    public Optional<Customer> getCustomerById(Long id) {
        return customerRepository.findById(id);
    }

    public Customer createCustomer(Customer customer) {
        return customerRepository.save(customer);
    }

    public Customer updateCustomer(Long id, Customer customer) {

        Customer existingCustomer = customerRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Customer not found"));

        existingCustomer.setCustomerId(customer.getCustomerId());
        existingCustomer.setTelecomPartner(customer.getTelecomPartner());
        existingCustomer.setGender(customer.getGender());
        existingCustomer.setAge(customer.getAge());
        existingCustomer.setState(customer.getState());
        existingCustomer.setCity(customer.getCity());
        existingCustomer.setNumDependents(customer.getNumDependents());
        existingCustomer.setEstimatedSalary(customer.getEstimatedSalary());
        existingCustomer.setCallsMade(customer.getCallsMade());
        existingCustomer.setSmsSent(customer.getSmsSent());
        existingCustomer.setDataUsed(customer.getDataUsed());
        existingCustomer.setTenureMonths(customer.getTenureMonths());
        existingCustomer.setRegistrationYear(customer.getRegistrationYear());
        existingCustomer.setChurn(customer.getChurn());

        return customerRepository.save(existingCustomer);
    }

    public void deleteCustomer(Long id) {
        customerRepository.deleteById(id);
    }
}