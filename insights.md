[Home](index.md) | [ETL](etl_pipeline.md) | [BPMN](BPMN.md) | [Insights](insights.md) | [Team](team_contb.md) | [About](About.md)
[Home](index.md) | [ETL](etl_pipeline.md) | [BPMN](BPMN.md) | [Insights](insights.md) | [Team](team_contb.md) | [About](About.md)

# Project Insights

This project helped us understand how healthcare data can be handled using real-world APIs and standards. We worked with multiple systems to simulate how patient information is shared between providers.

## What We Learned

- How to use FHIR APIs to fetch and post patient data.
- The importance of terminology standards like SNOMED and ICD-10.
- How to transform clinical concepts using parent and child relationships.
- How HL7 v2 messages work, and how to build them from FHIR resources.

## Technical Takeaways

- Adding `meta.profile` helped validate resources for FHIR compliance.
- Working with multiple systems (OpenEMR, Hermes, Primary Care EHR) required proper ID mapping and error handling.
- HL7 messages required structured formatting using segment rules (MSH, PID, etc).

## Challenges

- Some SNOMED concepts didn’t return expected mappings from Hermes.
- Rate limiting and slow responses from the APIs made debugging harder.
- Linking resources (like Procedure → Observation → Patient) needed attention to references.

## Overall

The project gave us hands-on experience with how data flows in healthcare systems and how standards are used to ensure interoperability between systems.
