# Troopsite Architecture and Requirements

## Project Status

Troopsite will be treated as a **brand new project**.

The existing FastAPI/SQLite application will **not** be ported or used as the architectural starting point. Existing code may be referenced for ideas if useful, but there is no requirement to preserve its routes, database schema, templates, or implementation.

## Purpose

Troopsite is a small website for a Girl Scout troop.

The site should provide troop families with:

- Announcements and troop news
- A troop roster
- Parent contact information
- Useful external links
- A clean, attractive, mobile-friendly interface

The site should remain simple to operate and maintain.

## Architecture Decision

Troopsite will be implemented as a **static website generated with Hugo**.

The project will not use:

- FastAPI
- SQLAlchemy
- SQLite
- A separate frontend application
- A persistent application server
- A database unless a future requirement clearly justifies one

Hugo will generate static HTML, CSS, and other assets for deployment.

## Technology Stack

### Site Generator

- Hugo
- Markdown for announcement content
- YAML for structured site data such as the roster and external links
- Hugo templates for page rendering
- Custom CSS for site styling

### Hosting

- DigitalOcean server
- Existing domain name
- DNS record pointing the desired hostname to the DigitalOcean server

A subdomain such as the following may be used:

```text
troop.example.com
```

The final hostname will be decided during deployment.

### Web Serving

The production request path should be:

```text
Internet
   |
   v
DNS
   |
   v
DigitalOcean
   |
   v
Traefik
   |
   v
nginx
   |
   v
Hugo-generated static site
```

Responsibilities:

- **Traefik**
  - Reverse proxy
  - HTTPS termination
  - Let's Encrypt certificate management
  - Authentication integration if needed

- **nginx**
  - Serves Hugo's generated static files

- **Hugo**
  - Generates the deployable website from Markdown, YAML, templates, and static assets

## Deployment Model

A Docker-based deployment is preferred.

The site may use a multi-stage image:

1. Build the site with Hugo.
2. Copy the generated `public/` directory into a small nginx image.
3. Run nginx behind the existing Traefik reverse proxy.

Conceptually:

```text
Git repository
      |
      v
   Hugo build
      |
      v
    public/
      |
      v
 nginx container
      |
      v
    Traefik
      |
      v
     HTTPS
```

There should be no database or application runtime required after the Hugo build completes.

## Content Model

### Announcements

Announcements will be authored as Markdown files.

Example:

```markdown
---
title: "Fall Campout"
date: 2026-10-02
category: "Camping"
---

Our fall campout will be October 24-25.

## What to bring

- Sleeping bag
- Water bottle
- Flashlight
- Warm clothes
```

Announcements should support at least:

- Title
- Publication date
- Markdown body
- Optional category or tag
- Optional featured status if useful later

### Homepage Announcements

The homepage should display approximately the **10 most recent announcements**.

Each entry should show enough information to quickly understand the announcement, such as:

- Title
- Date
- Short summary or excerpt
- Link to the full announcement

The homepage should include a link to view all announcements.

### Announcement Archive

All announcements should remain available after they fall off the homepage.

The announcement archive should:

- List all announcements
- Display newest announcements first
- Provide links to individual announcement pages

Older posts do not need to be manually moved into an archive directory. Hugo should generate the archive automatically from all announcement content.

Year-based archives may be added later if the number of posts becomes large.

## Roster

The site should include a troop roster.

The roster should contain information such as:

- Troop member name
- Grade
- Parent or guardian name
- Parent or guardian email address
- Parent or guardian phone number

The roster does not require a relational database.

Roster information should instead be stored as structured data, initially using YAML.

Example:

```yaml
members:
  - first_name: Alice
    last_name: Smith
    grade: 3
    parents:
      - Jane Smith
      - John Smith

parents:
  - name: Jane Smith
    email: jane@example.com
    phone: 555-555-1234
    members:
      - Alice Smith
```

The exact schema can be refined when the roster page is implemented.

## Roster Privacy

The roster contains personal information and must **not be exposed as an unrestricted public directory**.

This includes:

- Children's names
- Parent names
- Email addresses
- Phone numbers

Authentication or other access controls must be designed before the production roster is made available online.

Two possible approaches are acceptable:

### Option A — Protect the Entire Site

Require troop families to authenticate before viewing any part of the site.

This is the preferred simple model if the website is intended primarily for troop families.

### Option B — Public and Private Sections

Public content:

- General troop information
- Selected announcements
- External links
- Other intentionally public content

Private content:

- Roster
- Contact information
- Any announcement containing information that should only be available to troop families

Authentication may later be implemented through Traefik middleware and an authentication service such as Authelia or another suitable solution.

The authentication architecture will be decided separately before production deployment.

## External Links

The site should have a page for useful external resources.

Examples may include:

- Girl Scouts council website
- Volunteer Toolkit
- Cookie program resources
- Forms
- Camping resources
- Other troop-specific links

External links should be stored in structured data such as `data/links.yaml`.

Example:

```yaml
links:
  - name: Girl Scouts San Diego
    url: https://example.com/
    description: Council information and resources

  - name: Volunteer Toolkit
    url: https://example.com/
    description: Volunteer and troop planning resources
```

Important links may also appear on the homepage.

## Visual Design Requirements

The website should look polished and intentional, not like a default Hugo blog or developer documentation site.

The visual style should be:

- Friendly
- Welcoming
- Modern
- Appropriate for a Girl Scout troop
- Easy for parents to scan
- Mobile-first
- Colorful without being cluttered

A custom site design is preferred over using an off-the-shelf Hugo theme unchanged.

### General Visual Direction

Potential design elements include:

- Girl Scout-inspired green accents
- Dark green headings
- Warm or cream page backgrounds
- White content cards
- Rounded corners
- Subtle shadows
- Large, readable typography
- Good spacing
- Occasional troop-appropriate photos or illustrations

The site should not use excessive visual effects or unnecessary JavaScript.

## Responsive Design

The site must work well on phones.

This is especially important because parents are likely to access troop information from mobile devices.

### Roster

On larger screens, the roster may use a table.

Example:

```text
Member          Grade    Parent          Contact
------------------------------------------------------
Emma Jones        4      Sarah Jones     Email / Phone
Olivia Smith      3      Jane Smith      Email / Phone
```

On smaller screens, roster rows should transform into readable cards or another mobile-friendly layout rather than requiring horizontal scrolling.

### Navigation

Navigation should remain easy to use on small displays.

Expected top-level navigation may include:

- Home
- Announcements
- Roster
- Links

Additional sections can be added later.

## Homepage

The homepage should provide a useful overview rather than simply listing every page.

A likely layout is:

```text
Header / Navigation

Hero or Troop Introduction

Important or Upcoming Information

Latest Announcements
  - newest announcement
  - ...
  - approximately 10 total
  - View All Announcements

Useful Links

Footer
```

The hero section may include:

- Troop name or number
- Short troop description or motto
- Appropriate image or illustration
- Links to important areas of the site

## Proposed Project Layout

The initial Hugo repository may use a structure similar to:

```text
troopsite/
├── hugo.toml
├── content/
│   ├── _index.md
│   └── announcements/
│       ├── _index.md
│       └── example-announcement.md
├── data/
│   ├── roster.yaml
│   └── links.yaml
├── layouts/
│   ├── baseof.html
│   ├── index.html
│   ├── announcements/
│   │   ├── list.html
│   │   └── single.html
│   ├── roster/
│   └── links/
├── assets/
│   └── css/
│       └── styles.css
├── static/
│   └── images/
├── Dockerfile
├── compose.yaml
└── README.md
```

This is a starting structure rather than a rigid requirement.

## Design Principles

Future work should follow these principles:

1. **Keep the site static unless there is a strong reason not to.**
2. **Prefer Markdown for authored content.**
3. **Prefer simple YAML data files for small structured datasets.**
4. **Avoid introducing a database for data that can reasonably live in version-controlled files.**
5. **Avoid unnecessary JavaScript and frontend frameworks.**
6. **Make mobile usability a first-class requirement.**
7. **Protect troop family and child information from public exposure.**
8. **Favor simple deployment and low operational maintenance.**
9. **Use custom styling so the site feels polished and troop-specific.**
10. **Treat Git as the source of truth and history for site content and configuration.**

## Initial Development Scope

The first implementation should focus on:

1. Create a fresh Hugo project.
2. Create the base page layout and navigation.
3. Establish the site's visual design and responsive CSS.
4. Implement Markdown announcements.
5. Show the 10 newest announcements on the homepage.
6. Implement the complete announcement archive.
7. Implement structured external links.
8. Implement the roster from YAML data.
9. Make the roster responsive for desktop and mobile.
10. Build a production container using Hugo and nginx.
11. Configure deployment behind Traefik.
12. Design and implement appropriate access control before publishing private roster information.

## Explicit Non-Goals for the Initial Version

The initial site does not need:

- FastAPI
- SQLAlchemy
- SQLite
- REST APIs
- A JavaScript SPA
- React, Vue, or similar frontend frameworks
- User-editable web forms
- A content management system
- Dynamic server-side CRUD operations

If one of these capabilities becomes necessary in the future, it should be introduced based on an actual requirement rather than carried forward from the previous implementation.
