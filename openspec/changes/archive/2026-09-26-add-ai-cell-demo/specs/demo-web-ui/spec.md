# Spec Delta

## Purpose

A single-page demo interface through which the presenter and audience submit photos or select canned samples, watch detection overlays appear on the image, and read the AI's streamed narration, reachable from audience devices over the local network.

## ADDED Requirements

### Requirement: Single-page demo interface
The system SHALL present the entire demo (image submission, detection results, narration) on a single web page with a polished, dark-themed appearance suitable for projection.

#### Scenario: Presenter opens the demo page
- **WHEN** a browser loads the demo page
- **THEN** the page shows a title area, an image submission section with both upload and sample options, and result areas for detections and narration without further navigation

### Requirement: Image submission via upload or canned samples
The system SHALL accept an image either by file upload from the device or by selecting one of the bundled canned sample images.

#### Scenario: Uploading a photo
- **WHEN** the user selects a photo file and confirms the upload
- **THEN** the photo is displayed in the result area and analysis begins

#### Scenario: Selecting a canned sample
- **WHEN** the user clicks a canned sample thumbnail
- **THEN** the sample image is displayed in the result area and analysis begins

### Requirement: Detection overlay rendering
The system SHALL render detected regions as visual outlines drawn directly over the displayed image, aligned with the image as shown on screen.

#### Scenario: Displaying detection results
- **WHEN** an analysis returns one or more detected regions
- **THEN** each region is drawn as an outline over the corresponding part of the displayed image

### Requirement: Detection list with confidence
The system SHALL list each detected object with a human-readable label and its confidence level.

#### Scenario: Viewing detections
- **WHEN** an analysis returns detected objects
- **THEN** each object appears in a list with its label and confidence shown together

### Requirement: Progressively displayed narration
The system SHALL display AI narration text as it arrives, so that text appears progressively rather than all at once after a delay.

#### Scenario: Watching narration stream
- **WHEN** a narration is being generated
- **THEN** the narration area shows the text growing incrementally until complete

### Requirement: Visible analysis progress
The system SHALL show a visible in-progress state between image submission and the arrival of results.

#### Scenario: Waiting for analysis
- **WHEN** an image has been submitted and results have not yet arrived
- **THEN** the page indicates that analysis is in progress

### Requirement: Reachable from audience devices on the local network
The system SHALL be reachable from other devices on the same local network using the demo host's network address, not only from the host itself.

#### Scenario: Audience member opens the demo
- **WHEN** a device on the same local network opens the demo host's address in a browser
- **THEN** the demo page loads and is fully usable

### Requirement: Graceful upload errors
The system SHALL reject submitted files that are not images with an understandable message.

#### Scenario: Submitting a non-image file
- **WHEN** the user submits a file that is not a JPEG or PNG image
- **THEN** the page shows an error message and no analysis is performed
