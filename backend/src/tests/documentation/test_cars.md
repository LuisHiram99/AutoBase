# Cars Integration Tests Documentation

## Overview

The `TestCarsIntegration` class contains comprehensive integration tests for the cars API endpoints, testing the complete workflow from API requests to database operations.

## Test Fixtures

### Authentication Fixtures

- **`admin_user_token`** - Creates an admin user and returns authentication token
- **`manager_user_token`** - Creates a manager user and returns authentication token

### Helper Methods

- **`auth_headers(token)`** - Creates authorization headers for API requests

## Test Categories

### 1. Car Creation Tests

| Test Name                         | Description                                             |
| --------------------------------- | ------------------------------------------------------- |
| `test_create_car_as_admin`        | Admin user creating a car with full data validation     |
| `test_create_car_as_manager`      | Manager user creating a car (same permissions as admin) |
| `test_create_car_unauthenticated` | Creating car without authentication (should return 401) |
| `test_create_car_invalid_data`    | Testing data validation with missing/invalid fields     |

### 2. Car Retrieval Tests

| Test Name                       | Description                                             |
| ------------------------------- | ------------------------------------------------------- |
| `test_get_cars_as_admin`        | Admin user can see all cars in the system               |
| `test_get_cars_as_manager`      | Manager user can see all cars in the system             |
| `test_get_cars_pagination`      | Testing pagination with skip/limit parameters           |
| `test_get_cars_unauthenticated` | Getting cars without authentication (should return 401) |

### 3. Individual Car Retrieval Tests

| Test Name                       | Description                                            |
| ------------------------------- | ------------------------------------------------------ |
| `test_get_car_by_id_as_admin`   | Admin user can get any car by ID                       |
| `test_get_car_by_id_as_manager` | Manager user can get any car by ID                     |
| `test_get_car_not_found`        | Getting non-existent car returns 404                   |
| `test_get_car_unauthenticated`  | Getting car without authentication (should return 401) |

### 4. Car Update Tests

| Test Name                            | Description                                             |
| ------------------------------------ | ------------------------------------------------------- |
| `test_update_car_as_admin`           | Admin user can update any car (full update)             |
| `test_update_car_partial_as_manager` | Manager user can perform partial updates                |
| `test_update_car_not_found`          | Updating non-existent car returns 404                   |
| `test_update_car_unauthenticated`    | Updating car without authentication (should return 401) |
| `test_update_car_invalid_data`       | Testing validation with invalid update data             |

### 5. Car Deletion Tests

| Test Name                         | Description                                             |
| --------------------------------- | ------------------------------------------------------- |
| `test_delete_car_as_admin`        | Admin user can delete any car                           |
| `test_delete_car_as_manager`      | Manager user can delete any car                         |
| `test_delete_car_not_found`       | Deleting non-existent car returns 404                   |
| `test_delete_car_unauthenticated` | Deleting car without authentication (should return 401) |

### 6. Error Handling & Edge Cases

| Test Name                                    | Description                                                         |
| -------------------------------------------- | ------------------------------------------------------------------- |
| `test_create_duplicate_car`                  | Creating identical cars (should be allowed - no unique constraints) |
| `test_car_operations_comprehensive_workflow` | Complete CRUD workflow testing                                      |
| `test_rate_limiting_behavior`                | Testing API rate limiting behavior                                  |

## Test Statistics

- **Total Tests**: 24 integration tests
- **Authentication/Authorization Tests**: 8
- **CRUD Operation Tests**: 12 (4 create, 4 read, 5 update, 4 delete)
- **Error Handling/Validation Tests**: 5
- **Pagination Tests**: 1
- **Workflow Tests**: 2
- **Edge Case Tests**: 3

## Key Testing Patterns

### Role-based Access Control

- **Admin users**: Full access to all car operations
- **Manager users**: Full access to all car operations (no workshop restrictions for cars)
- **No Workshop Isolation**: Unlike customers, cars are not restricted by workshop

### Database Verification

Each test verifies that API operations are properly persisted to the database by:

1. Making API request
2. Checking response status and data
3. Querying database directly to confirm changes

### Car Data Model

Tests work with the Car schema which includes:

- **year**: Integer (required)
- **brand**: String (required)
- **model**: String (required)
- **car_id**: Auto-generated primary key

### Error Handling

Tests cover various error scenarios:

- Authentication failures (401)
- Not found errors (404)
- Validation errors (400/422)
- Rate limiting (429)

## Test Data Patterns

### Unique Identifiers

All test data uses unique identifiers to avoid conflicts:

- Car brands include test-specific prefixes
- Car models include context-specific names
- Years use different ranges per test

### No Workshop Restrictions

Unlike customer tests, car tests don't require workshop-specific logic:

- All authenticated users can access all cars
- No cross-workshop security testing needed
- Simpler test setup without workshop isolation

### Comprehensive CRUD Testing

Each major operation is tested with:

- Successful scenarios (admin and manager)
- Authentication failures
- Data validation
- Error conditions
- Database verification

## API Endpoints Tested

| Method | Endpoint                | Description                    |
| ------ | ----------------------- | ------------------------------ |
| POST   | `/api/v1/cars/`         | Create new car                 |
| GET    | `/api/v1/cars/`         | Get all cars (with pagination) |
| GET    | `/api/v1/cars/{car_id}` | Get specific car by ID         |
| PUT    | `/api/v1/cars/{car_id}` | Update car (full/partial)      |
| DELETE | `/api/v1/cars/{car_id}` | Delete car                     |

## Key Differences from Customer Tests

1. **No Workshop Restrictions**: Cars are global resources, not workshop-specific
2. **Equal Access**: Both admin and manager users have identical permissions
3. **Simpler Authorization**: No cross-workshop security concerns
4. **Duplicate Tolerance**: Multiple identical cars are allowed (no unique constraints)
5. **No Role Differentiation**: Admin and manager tests follow same patterns
