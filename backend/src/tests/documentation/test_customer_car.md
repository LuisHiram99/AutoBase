# Customer-Car Integration Tests Documentation

## Overview

The `TestCustomerCarIntegration` class contains comprehensive integration tests for the customer-car relationship API endpoints, testing the complete workflow from API requests to database operations. These tests validate the many-to-many relationship between customers and cars through the customer_car junction table.

## Test Fixtures

### Authentication Fixtures

- **`admin_user_token`** - Creates an admin user and returns authentication token
- **`manager_user_token`** - Creates a manager user and returns authentication token

### Data Setup Fixtures

- **`test_customer_and_car`** - Creates a test customer and car for relationship testing
- **`second_workshop_data`** - Creates a second workshop with customer and car for cross-workshop testing

### Helper Methods

- **`auth_headers(token)`** - Creates authorization headers for API requests

## Test Categories

### 1. Customer-Car Creation Tests

| Test Name                                             | Description                                                             |
| ----------------------------------------------------- | ----------------------------------------------------------------------- |
| `test_create_customer_car_as_admin`                   | Admin user creating customer-car relationship                           |
| `test_create_customer_car_as_manager_own_workshop`    | Manager user creating relationship for customer in their workshop       |
| `test_create_customer_car_manager_different_workshop` | Manager cannot create relationship for customer from different workshop |
| `test_create_customer_car_invalid_customer_id`        | Creating relationship with non-existent customer (should return 404)    |
| `test_create_customer_car_invalid_car_id`             | Creating relationship with non-existent car (should return 404)         |
| `test_create_customer_car_unauthenticated`            | Creating relationship without authentication (should return 401)        |
| `test_create_customer_car_invalid_data`               | Creating relationship with invalid/missing data (should return 400/422) |

### 2. Customer-Car Retrieval Tests

| Test Name                                             | Description                                                            |
| ----------------------------------------------------- | ---------------------------------------------------------------------- |
| `test_get_customer_cars_as_admin`                     | Admin user can see all customer-car relationships from all workshops   |
| `test_get_customer_cars_as_manager_own_workshop_only` | Manager user only sees relationships from their workshop               |
| `test_get_customer_cars_pagination`                   | Testing pagination with skip/limit parameters                          |
| `test_get_customer_cars_unauthenticated`              | Getting relationships without authentication (should return 401)       |
| `test_get_customer_car_by_id`                         | Getting specific customer-car relationship by ID with car information  |
| `test_get_customer_car_not_found`                     | Getting non-existent relationship returns 404                          |
| `test_get_customer_car_unauthenticated`               | Getting single relationship without authentication (should return 401) |

### 3. Customer-Car Update Tests

| Test Name                                   | Description                                                        |
| ------------------------------------------- | ------------------------------------------------------------------ |
| `test_update_customer_car`                  | Admin user updating customer-car relationship                      |
| `test_update_customer_car_invalid_customer` | Updating relationship with invalid customer ID (should return 404) |
| `test_update_customer_car_invalid_car`      | Updating relationship with invalid car ID (should return 404)      |
| `test_update_customer_car_not_found`        | Updating non-existent relationship (should return 404)             |
| `test_update_customer_car_unauthenticated`  | Updating relationship without authentication (should return 401)   |

### 4. Customer-Car Deletion Tests

| Test Name                                  | Description                                                      |
| ------------------------------------------ | ---------------------------------------------------------------- |
| `test_delete_customer_car`                 | Admin user deleting customer-car relationship                    |
| `test_delete_customer_car_not_found`       | Deleting non-existent relationship (should return 404)           |
| `test_delete_customer_car_unauthenticated` | Deleting relationship without authentication (should return 401) |

### 5. Comprehensive Workflow Tests

| Test Name                             | Description                                                           |
| ------------------------------------- | --------------------------------------------------------------------- |
| `test_complete_customer_car_workflow` | Full CRUD workflow: Create → Read → Update → Delete → Verify deletion |
| `test_multiple_cars_per_customer`     | Testing that one customer can have multiple car relationships         |
| `test_same_car_multiple_customers`    | Testing that one car can be associated with multiple customers        |

## Test Statistics

- **Total Tests**: 25 integration tests
- **Authentication/Authorization Tests**: 6
- **CRUD Operation Tests**: 17 (7 create, 7 read, 5 update, 3 delete)
- **Role-based Access Control Tests**: 9
- **Cross-workshop Security Tests**: 3
- **Error Handling/Validation Tests**: 8
- **Pagination Tests**: 1
- **Business Logic/Workflow Tests**: 3

## Key Testing Patterns

### Role-based Access Control

- **Admin users**: Can access all customer-car relationships across workshops
- **Manager users**: Can only access relationships for customers in their own workshop
- **Cross-workshop restrictions**: Managers cannot create relationships for customers from other workshops

### Database Verification

Each test verifies that API operations are properly persisted to the database by:

1. Making API request
2. Checking response status and data
3. Querying database directly to confirm changes
4. Verifying relationship integrity

### Customer-Car Relationship Validation

Tests ensure proper many-to-many relationship handling:

- Customer-car relationships include license plate and color information
- Car information is properly joined and returned (brand, model, year)
- Multiple relationships per customer are supported
- Multiple customers per car are supported

### Cross-workshop Security

Tests ensure proper isolation between workshops:

- Managers cannot access customer-car relationships from other workshops
- Admins can access all relationships regardless of workshop
- Customer validation respects workshop boundaries

### Error Handling

Tests cover various error scenarios:

- Authentication failures (401)
- Authorization failures (404 for cross-workshop access)
- Validation errors (400/422/429)
- Foreign key constraint violations (404 for invalid IDs)
- Missing required fields

## Test Data Patterns

### Unique Identifiers

All test data uses unique identifiers to avoid conflicts:

- License plates include test-specific prefixes (ABC-123, XYZ-789, etc.)
- Colors use descriptive test names
- Email addresses include test context prefixes

### Dynamic ID References

Tests use fixture-generated IDs to avoid hardcoded references:

- Customer IDs from `test_customer_and_car` fixture
- Car IDs from database-created entities
- Workshop IDs from `_setup_workshop` fixture

### Rate Limiting Considerations

Tests include rate limiting awareness:

- Flexible assertions that account for potential 429 responses
- Error counting and minimum success validation
- Debug output for failed requests

## API Response Structure

### CustomerCar Response

```json
{
  "customer_car_id": 1,
  "customer_id": 123,
  "car_id": 456,
  "license_plate": "ABC-123",
  "color": "Blue"
}
```

### CustomerCarWithCarInfo Response

```json
{
  "customer_car_id": 1,
  "customer_id": 123,
  "car_id": 456,
  "license_plate": "ABC-123",
  "color": "Blue",
  "car_brand": "Toyota",
  "car_model": "Camry",
  "car_year": 2023
}
```

## Business Logic Validation

### One-to-Many Relationships

- **Customer → Multiple Cars**: One customer can have relationships with multiple cars
- **Car → Multiple Customers**: One car can be associated with multiple customers
- **License Plate Uniqueness**: Each relationship has its own license plate and color

### Workshop Isolation

- **Manager Restrictions**: Managers can only manage relationships for customers in their workshop
- **Admin Access**: Admins have global access across all workshops
- **Customer Validation**: Customer must exist in accessible workshop before creating relationship

### Data Integrity

- **Foreign Key Validation**: Both customer_id and car_id must reference existing records
- **Required Fields**: license_plate is mandatory for all relationships
- **Optional Fields**: color is optional but commonly used
