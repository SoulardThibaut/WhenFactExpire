SELECT DISTINCT ?h ?r ?v ?start ?end
WHERE {
        FILTER(strstarts(str(?statement), "http://www.wikidata.org/entity/statement/"))
        FILTER(strstarts(str(?rs), "http://www.wikidata.org/prop/statement/P"))
        FILTER((strlen(str(?start))>0) || (strlen(str(?end))>0))
        ?h ?r ?statement.
        ?statement ?rs ?v.
        OPTIONAL{
                ?statement <http://www.wikidata.org/prop/qualifier/P580> ?start.
                FILTER(datatype(?start) = <http://www.w3.org/2001/XMLSchema#dateTime>)
        }
        OPTIONAL{
                ?statement <http://www.wikidata.org/prop/qualifier/P582> ?end.
                FILTER(datatype(?end) = <http://www.w3.org/2001/XMLSchema#dateTime>)
        }
}
