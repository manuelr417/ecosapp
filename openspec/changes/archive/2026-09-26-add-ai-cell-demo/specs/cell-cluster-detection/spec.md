# Spec Delta

## Purpose

Act 2 of the demo: detect and annotate cell clusters in microscopy images via a hosted detection service, with pre-computed annotations for the lab-owned rehearsal images so the core demo moment works even without connectivity.

## ADDED Requirements

### Requirement: Detect cell clusters in microscopy images
The system SHALL analyze a submitted microscopy image and return detected cell clusters, each with its region in the image, suitable for drawing cluster outlines.

#### Scenario: Microscopy image with visible clusters
- **WHEN** a microscopy image containing cell clusters is submitted while the hosted detection service is reachable
- **THEN** the response contains regions for the detected clusters

### Requirement: Pre-computed annotations for rehearsal images
For each designated lab-owned sample image, the system SHALL serve a pre-computed annotation when the hosted detection service is unreachable.

#### Scenario: Rehearsal image while offline
- **WHEN** a designated lab-owned sample image is submitted and the hosted detection service cannot be reached
- **THEN** the system returns that image's pre-computed cluster annotations

### Requirement: Explicit failure for live images while offline
The system SHALL return an explicit service-unavailable error when a non-sample microscopy image is submitted and the hosted detection service is unreachable, rather than returning empty or incorrect results.

#### Scenario: Live audience image while offline
- **WHEN** an image that has no pre-computed annotation is submitted and the hosted detection service cannot be reached
- **THEN** the response is an explicit service-unavailable error that the interface can display

### Requirement: Hosted service errors are visible
The system SHALL surface errors from the hosted detection service as explicit failures rather than presenting them as empty detection results.

#### Scenario: Hosted service returns an error
- **WHEN** the hosted detection service responds with an error
- **THEN** the system reports a failure to the caller instead of zero detections

### Requirement: In-memory processing only
The system SHALL process submitted microscopy images in memory and MUST NOT persist submitted images or their annotations to disk.

#### Scenario: No files left behind
- **WHEN** any microscopy image is submitted and analyzed
- **THEN** no copy of the image is written to the demo host's disk
