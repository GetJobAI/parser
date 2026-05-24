from app.job.pipeline import JobPostingPipeline


def test_job_posting_pipeline_uses_json_ld_and_section_headings():
    html = """
    <html>
      <head>
        <title>Senior Backend Engineer - Example Corp</title>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "JobPosting",
          "title": "Senior Backend Engineer",
          "employmentType": "FULL_TIME",
          "hiringOrganization": {"@type": "Organization", "name": "Example Corp"},
          "jobLocation": {
            "@type": "Place",
            "address": {
              "@type": "PostalAddress",
              "addressLocality": "Berlin",
              "addressCountry": "DE"
            }
          }
        }
        </script>
      </head>
      <body>
        <h1>Senior Backend Engineer</h1>
        <p>Join our platform team building reliable APIs for millions of users.</p>
        <h2>Responsibilities</h2>
        <ul>
          <li>Build FastAPI services and PostgreSQL-backed APIs.</li>
          <li>Own Docker and Kubernetes deployment workflows.</li>
        </ul>
        <h2>Requirements</h2>
        <ul>
          <li>Strong Python and SQL skills.</li>
          <li>Experience with AWS and CI/CD pipelines.</li>
        </ul>
        <h2>Nice to have</h2>
        <ul>
          <li>Exposure to Terraform.</li>
        </ul>
        <h2>Benefits</h2>
        <ul>
          <li>Remote-first culture.</li>
        </ul>
      </body>
    </html>
    """
    pipeline = JobPostingPipeline(parser_version="test")
    content, report = pipeline.parse(html=html, source_url="https://example.com/jobs/1")

    assert content.meta.parse_status == "completed"
    assert content.meta.structured_data_used is True
    assert content.title == "Senior Backend Engineer"
    assert content.company == "Example Corp"
    assert content.location == "Berlin, DE"
    assert content.employment_type == "full_time" or content.employment_type == "full-time" or content.employment_type == "full time"
    assert "Build FastAPI services and PostgreSQL-backed APIs" in content.responsibilities
    assert "Strong Python and SQL skills" in content.requirements
    assert "Exposure to Terraform" in content.preferred_requirements
    assert "Remote-first culture" in content.benefits
    assert set(content.skills) >= {"Python", "SQL", "PostgreSQL", "FastAPI", "Docker", "Kubernetes", "AWS", "CI/CD", "Terraform"}
    assert "requirements" in report.major_sections_found


def test_job_posting_pipeline_handles_plain_html_without_structured_data():
    html = """
    <html>
      <head>
        <meta name="description" content="Acme is hiring a Product Designer to shape web experiences." />
      </head>
      <body>
        <main>
          <h1>Product Designer</h1>
          <p>Acme</p>
          <p>Location: Warsaw, Poland · Hybrid</p>
          <p>Salary: EUR 3000 - 4500 / month</p>
          <h2>What you'll do</h2>
          <ul>
            <li>Design flows and interface concepts in Figma.</li>
            <li>Collaborate with engineers and product managers.</li>
          </ul>
          <h2>Qualifications</h2>
          <ul>
            <li>Experience with design systems.</li>
            <li>Strong communication skills.</li>
          </ul>
        </main>
      </body>
    </html>
    """
    pipeline = JobPostingPipeline(parser_version="test")
    content, report = pipeline.parse(html=html)

    assert content.title == "Product Designer"
    assert content.company == "Acme"
    assert content.location == "Location: Warsaw, Poland · Hybrid" or content.location == "Warsaw, Poland · Hybrid"
    assert content.work_mode == "hybrid"
    assert content.salary == "EUR 3000 - 4500 / month"
    assert content.summary is not None
    assert "Design flows and interface concepts in Figma" in content.responsibilities
    assert "Experience with design systems" in content.requirements
    assert "Figma" in content.skills
    assert report.partial_parse is False


def test_job_posting_pipeline_handles_plain_text_input():
    text = """
    Junior Data Analyst
    Bright Metrics
    Remote

    Overview
    Join our analytics team and support stakeholders with reporting.

    Responsibilities
    - Build dashboards in SQL and Python.
    - Present insights to business teams.

    Requirements
    - Strong SQL knowledge.
    - Familiarity with Python and Excel.

    Benefits
    - Flexible schedule.
    """
    pipeline = JobPostingPipeline(parser_version="test")
    content, report = pipeline.parse(text=text)

    assert content.title == "Junior Data Analyst"
    assert content.company == "Bright Metrics"
    assert content.work_mode == "remote"
    assert content.seniority == "junior"
    assert "Build dashboards in SQL and Python" in content.responsibilities
    assert set(content.skills) >= {"SQL", "Python"}
    assert "benefits" in report.major_sections_found
