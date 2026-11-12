# Recorded fixtures

`lit/` holds the thirteen HTTP responses `tests/test_lit.py` serves to `tools/lit.py` in place of the network: real
answers from OpenAlex (`oa_*.json`), Semantic Scholar (`s2_*.json`), arXiv (`arxiv_search.xml`,
`landing_arxiv_abs.html`) and Unpaywall (`upw_*.json`), captured 2026-10-02, and one bot-challenge page a university
repository served in place of a paper's landing page (`landing_anubis.html`, issued 2026-10-03 UTC). No test touches
the network; a fixture changes only by a new capture, recorded here with its date.

Three files differ from what the services sent, so that this tree carries no address and no private-host shape; no
test reads any of the edited values:

- `landing_anubis.html`: the client's IP address was replaced by a documentation address at capture; the User-Agent
  the challenge echoes back was replaced by a neutral one of the same shape, and the contact address in the page's
  licence notice by the marker `<address removed>`.
- `oa_search.json`: one author's affiliation string, in both fields that carry it, was trimmed to the institution —
  the city and postal code dropped.
- `oa_work_brown2010.json`: two `locations` entries from CiteSeerX were deleted, because CiteSeerX identifiers have
  the shape of private IPv4 addresses, which the privacy checks on this tree refuse; the two remaining entries, and
  `best_oa_location` and `primary_location`, are as recorded.
