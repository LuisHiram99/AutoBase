# Customer Integration Tests Documentation

## Overview

The `TestCustomersIntegration` class contains comprehensive integration tests for the customers API endpoints, testing the complete workflow from API requests to database operations.

## Test Fixtures

### Authentication Fixtures

- **`admin_user_token`** - Creates an admin user and returns authentication token
- **`manager_user_token`** - Creates a manager user and returns authentication token
- **`second_workshop`** - Creates a second workshop for testing cross-workshop access

### Helper Methods

- **`auth_headers(token)`** - Creates authorization headers for API requests
- **`get_default_workshop_id(db_session)`** - Retrieves the default workshop ID

## Test Categories

### 1. Customer Creation Tests

| Test Name                                                | Description                                                         |
| -------------------------------------------------------- | ------------------------------------------------------------------- |
| `test_create_customer_as_admin_with_workshop_id`         | Admin user creating customer with specified workshop_id             |
| `test_create_customer_as_manager_without_workshop_id`    | Manager user creating customer (auto-assigned to their workshop)    |
| `test_create_customer_worker_cannot_specify_workshop_id` | Manager users cannot specify workshop_id (should return 400)        |
| `test_create_customer_admin_must_specify_workshop_id`    | Admin users must specify workshop_id (should return 400 without it) |
| `test_create_customer_unauthenticated`                   | Creating customer without authentication (should return 401)        |

### 2. Customer Retrieval Tests

| Test Name                                          | Description                                          |
| -------------------------------------------------- | ---------------------------------------------------- |
| `test_get_customers_as_admin`                      | Admin user can see all customers from all workshops  |
| `test_get_customers_as_worker_only_own_workshop`   | Manager user only sees customers from their workshop |
| `test_get_customers_pagination`                    | Testing pagination with skip/limit parameters        |
| `test_get_customer_by_id_as_admin`                 | Admin user can get any customer by ID                |
| `test_get_customer_by_id_worker_own_workshop_only` | Manager can only get customers from their workshop   |
| `test_get_customer_not_found`                      | Getting non-existent customer returns 404            |

### 3. Customer Update Tests

| Test Name                                               | Description                                           |
| ------------------------------------------------------- | ----------------------------------------------------- |
| `test_update_customer_as_admin`                         | Admin user can update any customer                    |
| `test_update_customer_worker_cannot_change_workshop_id` | Manager cannot update workshop_id (should return 403) |
| `test_update_customer_worker_own_workshop_only`         | Manager can only update customers in their workshop   |

### 4. Customer Deletion Tests

| Test Name                                       | Description                                           |
| ----------------------------------------------- | ----------------------------------------------------- |
| `test_delete_customer_as_admin`                 | Admin user can delete any customer                    |
| `test_delete_customer_worker_own_workshop_only` | Manager can only delete customers from their workshop |

### 5. Customer-Car Relationship Tests

| Test Name                           | Description                                                 |
| ----------------------------------- | ----------------------------------------------------------- |
| `test_add_car_to_customer`          | Adding a car to a customer (customer-car relationship)      |
| `test_get_customer_cars`            | Getting all cars associated with a customer                 |
| `test_get_customer_cars_empty_list` | Getting cars for customer with no cars (returns empty list) |

### 6. Error Handling & Validation Tests

| Test Name                                            | Description                                             |
| ---------------------------------------------------- | ------------------------------------------------------- |
| `test_create_customer_duplicate_email_same_workshop` | Testing duplicate email validation                      |
| `test_create_customer_invalid_workshop_id`           | Testing invalid workshop_id handling                    |
| `test_invalid_customer_data_validation`              | Testing data validation (missing fields, invalid email) |

## Test Statistics

- **Total Tests**: 22 integration tests
- **Authentication/Authorization Tests**: 7
- **CRUD Operation Tests**: 11 (5 create, 4 read, 2 update, 2 delete)
- **Role-based Access Control Tests**: 8
- **Customer-Car Relationship Tests**: 3
- **Error Handling/Validation Tests**: 3
- **Cross-workshop Security Tests**: 6
- **Pagination Tests**: 1

## Key Testing Patterns

### Role-based Access Control

- **Admin users**: Can access all customers across workshops, must specify `workshop_id` when creating
- **Manager users**: Can only access customers in their own workshop, cannot specify `workshop_id` when creating

### Database Verification

Each test verifies that API operations are properly persisted to the database by:

1. Making API request
2. Checking response status and data
3. Querying database directly to confirm changes

### Cross-workshop Security

Tests ensure proper isolation between workshops:

- Managers cannot access customers from other workshops
- Admins can access all customers regardless of workshop

### Error Handling

Tests cover various error scenarios:

- Authentication failures (401)
- Authorization failures (403/404)
- Validation errors (400/422)
- Rate limiting (429)
- Server errors (500)

## Test Data Patterns

### Unique Identifiers

All test data uses unique identifiers to avoid conflicts:

- Workshop names include test-specific suffixes
- Customer emails include test context prefixes
- Phone numbers use distinct ranges per test

### Dynamic Workshop IDs

Tests use `get_default_workshop_id()` to avoid hardcoded workshop references and prevent primary key conflicts.
