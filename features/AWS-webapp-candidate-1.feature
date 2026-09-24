Feature: Contact Page Submission

  Scenario: Display the contact form
    Given the visitor accesses the application URL
    When the page loads
    Then the contact form is displayed

  Scenario: Successful form submission
    Given the visitor fills in the contact form with valid first name, last name, email address, and message
    When the visitor submits the form
    Then the application saves the submission to DynamoDB
    And the confirmation page is displayed

  Scenario: Submission with missing fields
    Given the visitor fills in the contact form with missing first name
    When the visitor submits the form
    Then an error message is displayed indicating the missing field
    And the submission is not saved

  Scenario: Submission with invalid email
    Given the visitor fills in the contact form with an invalid email address
    When the visitor submits the form
    Then an error message is displayed indicating the invalid email
    And the submission is not saved

  Scenario: Database failure during submission
    Given the visitor fills in the contact form with valid details
    When the visitor submits the form and a database error occurs
    Then an error message is displayed indicating a submission failure
    And the submission is not saved
