# Requirements Specification
## SCLAPP System

---

# 1. Functional Requirements

## RF01 – User Registration
The system must allow registering new users by providing basic information such as full name, identification number, username, email address, and password.

## RF02 – User Login
The system must allow users to authenticate using their username or email address and password.

## RF03 – Session Management
The system must generate access tokens and refresh tokens to maintain authenticated sessions.

## RF04 – Role Management
The system must assign a role to each user in order to control their access level within the system.

## RF05 – Company Management
The system must allow registering companies with information such as name, sector, email, phone, country, address, and description.

## RF06 – Company Update
The system must allow modifying the information of registered companies.

## RF07 – Company Status Management
The system must allow changing the status of a company among the predefined statuses in the system.

## RF08 – Technology Association
The system must allow associating one or more technologies with a company.

## RF09 – Scraping Execution
The system must allow executing scraping processes to collect company information from external sources.

## RF10 – Scraping Log Registration
The system must store logs for each scraping execution, including parameters used, number of results found, and execution status.

## RF11 – Email Sending
The system must allow sending emails to companies directly from the platform.

## RF12 – Email History
The system must store and allow users to view the history of emails sent to companies.

## RF13 – Email Event Tracking
The system must record events related to email delivery, such as sent, delivered, or failed.

## RF14 – Dashboard
The system must provide a dashboard where users can visualize company data, scraping activity, and email activity.

## RF15 – User Profile Management
The system must allow users to view and update their profile information.
