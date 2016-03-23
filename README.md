# washroom
This is the videorooter washroom; washing, drying &amp; folding data
sources (aka ETL). The repository gives an overview of the process we
go through, but individual repositories carry the actual code for
doing so.

Videorooter follow roughly the following steps for its work on
producing a finished data set:

 * Routinely retrieve new and changed works from a data source.
 * Translate the information from the data source into a format used
   by Videorooter. This includes any changes or adjustments that need
   to be made to the data.
 * Load this information into the Videorooter database.

You will be most interested in:

 docs/db/  The database model of Videorooter, the way in which the data
          should be structured when loaded into Videorooter.
