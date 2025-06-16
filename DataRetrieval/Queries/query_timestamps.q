SELECT DISTINCT ?h ?r ?v ?point
WHERE {
        FILTER(strstarts(str(?r), "http://www.wikidata.org/prop/P"))
        FILTER(strstarts(str(?statement), "http://www.wikidata.org/entity/statement/"))
        ?h ?r ?statement.

        FILTER(strstarts(str(?rs), "http://www.wikidata.org/prop/statement/P"))
        ?statement ?rs ?v.

        FILTER(datatype(?point) = <http://www.w3.org/2001/XMLSchema#dateTime>)
        ?statement <http://www.wikidata.org/prop/qualifier/P585> ?point
}