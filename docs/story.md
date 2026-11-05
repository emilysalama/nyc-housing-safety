## The question

New York never stops building. Between 2022 and mid-2026, New Yorkers saw tens of thousands of new-building filings, along with demolitions, sidewalk sheds, and curb cuts. At the same time, the city’s streets carry the traffic that moves its 8 million residents, and some crashes leave people seriously injured or dead. These two worlds are usually studied separately: housing agencies track permits, transportation agencies track crashes.

We ask: do the neighborhoods with the most construction activity also see more serious street crashes, and does that pattern hold across years, boroughs, and types of crashes? We do not assume construction causes crashes. We want to know whether the two move together, where they overlap, and where safety attention may be lagging behind growth. Housing and street safety are managed by different agencies using different data. If areas with heavy construction also see more serious crashes, planners could pair new development with street-safety attention early; if they don’t, safety effort can go to where crashes actually cluster. Either answer helps residents, the DOT, and community boards decide where to act first.

## The data

Housing: DOB NOW: Build Job Application Filings (NYC Open Data), filings dated January 2022 to June 2026. We use the property’s ZIP code (not the applicant’s office ZIP), keep one record per job, and measure construction through new buildings, full demolitions, alteration filings, proposed dwelling units, and street-facing work such as sidewalk sheds and curb cuts. [UPDATE after Member 1 confirms: “No Work” filings and “ALT-CO - New Building with Existing Elements to Remain” filings are excluded from the new-building measure.]

Crashes: the DOT’s Serious Injury Response, Tracking and Analysis Program (SIRTA), covering serious-injury and fatal crashes from January 2022 to June 2026. After removing 444 empty rows and 1 duplicate, 13,309 crashes remain. [UPDATE if the final count changes.]

How we connected them: the two datasets share no key, so we compare areas, not individual records. We aggregate both to ZIP code by year (2022 to 2025, complete years only) and to borough by month (January 2022 to June 2026). ZIP is the finest area both datasets have, and we stop at yearly counts for ZIPs because SIRTA averages only one or two crashes per ZIP per month. A row-level join would pair events that have no real connection.

Cleaning: 39% of crashes had no ZIP code. We recovered ZIPs from crash coordinates using a spatial join against ZIP boundaries. Housing data had placeholder codes (for example, 998 and 999 for dwelling units), text-formatted numbers, and repeated filings, which we corrected or removed. [UPDATE with Member 1 and Member 2’s final numbers.]

## The limits

- Serious crashes only. SIRTA covers crashes the DOT analyzed for serious injury or death, not all crashes. Our results say nothing about minor collisions.
- Missing locations are not random. Of the usable crashes, 61% carried a ZIP, 31% were assigned one from coordinates, and 9% could only be placed by borough, or not at all. About 31% of those unlocated crashes involved a fatality, versus about 6% of the rest, so ZIP-level fatality counts are understated. ZIP coverage also varied by year (only 16% of 2022 crashes had a ZIP on record, versus 68 to 80% later), so year-to-year changes can partly reflect how well crashes were located. [UPDATE with figures from coverage_report.csv.]
- Highway crashes are only partly separated. We flag a crash as a highway crash only if the data lists a highway reference marker (7.9% of crashes), so some highway crashes remain in our “street crash” counts.
- Filings are paperwork, not buildings. A filing shows intent and timing, not what was built, how large it was, or when work started.
- Busy places have more of everything. We have no population or traffic-volume data, so ZIPs with more activity can show more filings and more crashes for the same reason. ZIP areas also differ widely in size.
- Short window. Four full years (2022 to 2025) cannot show long-term trends and 2022 may still reflect post-pandemic traffic patterns.
- Associations, not causes. Nothing here shows that construction causes crashes.

## The discovery

TODO (Saturday): what we found and what surprised us, from the final charts.

## What it means for NYC

TODO (Saturday): who can use these findings and what they should do differently.