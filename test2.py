# import SPARQL-parser as SPARQL
import SPARQL_parser as SPARQL


sparql_query='SELECT DISTINCT ?uri WHERE { ?x <http://dbpedia.org/property/international> <http://dbpedia.org/resource/Muslim_Brotherhood> . ?x <http://dbpedia.org/ontology/religion> ?uri  . ?x <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/PoliticalParty>}'
a=SPARQL(sparql_query)
a.where




