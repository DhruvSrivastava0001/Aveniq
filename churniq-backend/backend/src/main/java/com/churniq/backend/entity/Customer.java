package com.churniq.backend.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "customers")
public class Customer {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String customerId;

    private String telecomPartner;

    private String gender;

    private Integer age;

    private String state;

    private String city;

    private Integer numDependents;

    private Double estimatedSalary;

    private Integer callsMade;

    private Integer smsSent;

    private Double dataUsed;

    private Integer tenureMonths;

    private Integer registrationYear;

    private Integer churn;

    private Integer pincode;
    private java.time.LocalDate dateOfRegistration;

    public Customer() {

        
    }

    public Integer getPincode() {
    return pincode;
}

public void setPincode(Integer pincode) {
    this.pincode = pincode;
}

public java.time.LocalDate getDateOfRegistration() {
    return dateOfRegistration;
}

public void setDateOfRegistration(
        java.time.LocalDate dateOfRegistration) {
    this.dateOfRegistration = dateOfRegistration;
}






    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getCustomerId() {
        return customerId;
    }

    public void setCustomerId(String customerId) {
        this.customerId = customerId;
    }

    public String getTelecomPartner() {
        return telecomPartner;
    }

    public void setTelecomPartner(String telecomPartner) {
        this.telecomPartner = telecomPartner;
    }

    public String getGender() {
        return gender;
    }

    public void setGender(String gender) {
        this.gender = gender;
    }

    public Integer getAge() {
        return age;
    }

    public void setAge(Integer age) {
        this.age = age;
    }

    public String getState() {
        return state;
    }

    public void setState(String state) {
        this.state = state;
    }

    public String getCity() {
        return city;
    }

    public void setCity(String city) {
        this.city = city;
    }

    public Integer getNumDependents() {
        return numDependents;
    }

    public void setNumDependents(Integer numDependents) {
        this.numDependents = numDependents;
    }

    public Double getEstimatedSalary() {
        return estimatedSalary;
    }

    public void setEstimatedSalary(Double estimatedSalary) {
        this.estimatedSalary = estimatedSalary;
    }

    public Integer getCallsMade() {
        return callsMade;
    }

    public void setCallsMade(Integer callsMade) {
        this.callsMade = callsMade;
    }

    public Integer getSmsSent() {
        return smsSent;
    }

    public void setSmsSent(Integer smsSent) {
        this.smsSent = smsSent;
    }

    public Double getDataUsed() {
        return dataUsed;
    }

    public void setDataUsed(Double dataUsed) {
        this.dataUsed = dataUsed;
    }

    public Integer getTenureMonths() {
        return tenureMonths;
    }

    public void setTenureMonths(Integer tenureMonths) {
        this.tenureMonths = tenureMonths;
    }

    public Integer getRegistrationYear() {
        return registrationYear;
    }

    public void setRegistrationYear(Integer registrationYear) {
        this.registrationYear = registrationYear;
    }

    public Integer getChurn() {
        return churn;
    }

    public void setChurn(Integer churn) {
        this.churn = churn;
    }
}