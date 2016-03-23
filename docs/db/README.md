# Database model

This is the basic database model for Videorooter. You'll note it's
rather simple as such: it does not try to be much more than what is
needed to do the job. Much of the information is also stored in text
columns which in principle could have any value.

## A note on terminology

Let's first consider what it is we're recording in the database. The 
Functional Requirements for Bibliographic Records (FRBR)
recommendation from the International Federation of Library
Associations and Institutions (IFLA) outline the following terminology:

  * Work is a "distinct intellectual or artistic creation."
  * Expression is "the specific intellectual or artistic form a
    work takes each time it is 'realized.'"
  * Manifestation is "the physical embodiment of an expression of a
    work."

So for instance, a Work could be *The Tragedy of Macbeth* by *William
Shakespeare*. There would be many expressions of it, including both
the *First* and *Second* Folio of the collected plays of William
Shakespeare. Each Folio would be its own expression, and each physical
copy of the Folio would be a unique manifestation of it.

For the digital videos and images we consider, we don't (yet) make any
attempt at deriving the Work from them. Instead, our data model starts
with the Expression. If the same video is posted multiple
times (for instance both on Wikipedia and through some collection
indexed in Europeana), we treat those as being different Expressions.

The Manifestation is the URL to the specific video. Each
Expression could have multiple Manifestations, for instance as is the
case with Internet Archive where each video is available in different
encoding formats. This would generate one Expression with one
Manifestation for each encoding of the video.

## Database tables

### expression

| Column | Type | Explanation |
| --- | --- | --- |
| expression_id | integer | Sequence, starting at 1 |
| title | varchar(250) | The title of an expression |
| description | varchar(2048) | |
| rights_statement | varchar(128) | A URI indicating the Creative Commons license or other rights statement relevant |
| media_type | varchar(64) | The specific media type, for instance video/ogg |
| credit | varchar(256) | The author or holder of copyright to which credit is to be given on re-use |
| credit_url | varchar(1024) | The URL associated to link to on re-use |
| updated_date | timestamp | Laste updated date |
| collection_uri | varchar(128) | The URI of a collection identifier |
| source_url | varchar(128) | The source URL where the expression has been found |

### manifestation

| Column | Type | Explanation |
| --- | --- | --- |
| url | varchar(1024) | The URL where the expression is manifested |
| expression_id_expression | integer | Reference to the expression table |

### fingerprint

| Column | Type | Explanation |
| --- | --- | --- |
| type | varchar(64) | A URN describing the type of hash |
| hash | varchar(512) | The specific hash (type dependent) |
| updated_date | timestamp | Last updated date |
| url_manifestation | varchar(1024) | Reference to the manifestation table |

## Rights statements

Videorooter supports the full set of Creative Commons' licenses using
their URL as the URI for a rights statement, as well as the rights
statements outlined in the Europeana and DPLA white paper
*Recommendations for Standardized International Rights Statements*.

## Fingerprint types

The following fingerprint types are known:

| URN | Name | Media types | Specification | Implementation 1 | Implementation 2 |
| --- | --- | --- | --- | --- | --- |
| urn:blockhash | blockhash perceptual hash algorithm | image/* | https://github.com/commonsmachinery/blockhash-rfc/blob/master/draft-commonsmachinery-urn-blockhash-00.txt | https://github.com/commonsmachinery/blockhash | https://github.com/commonsmachinery/blockhash-python |
| urn:x-bhvideo-phash | video blockhash with phash fingerprints | video/* | NONE | https://github.com/ivanp2015/blockhash/tree/phash-exp | NONE |
