from pyparsing import Word, Suppress, Optional, alphanums, Group, ZeroOrMore, Keyword, Literal, \
                      CaselessLiteral, nums, Combine, alphas, nestedExpr, cppStyleComment, OneOrMore, \
                      quotedString, LineEnd, StringEnd, restOfLine, delimitedList, dictOf, Forward, Dict


lbrace = Suppress("{")
rbrace = Suppress("}")
lbracket = Suppress("[")
rbracket = Suppress("]")
lparen = Suppress("(")
rparen = Suppress(")")
equal = Suppress("=")
comma = Suppress(",")
point = Literal('.')
tilde = ('~')
bang = ('!')
e = CaselessLiteral('E')
plusorminus = Literal('+') | Literal('-')
hashsymbol = Suppress("#")
dbquotes = '"'

uni_arrow = Literal("->")
bi_arrow = Literal("<->")

# molecule keywords
define_molecules_ = Keyword("DEFINE_MOLECULES")
diffusion_constant_3d_ = Keyword("DIFFUSION_CONSTANT_3D")
diffusion_constant_2d_ = Keyword("DIFFUSION_CONSTANT_2D")

#reaction keywords
define_reactions_ = Keyword("DEFINE_REACTIONS")

#seed species keywords
instantiate_ = Keyword("INSTANTIATE")
object_ = Keyword("OBJECT")
parent_ = Keyword("PARENT")
release_site_ = Keyword("RELEASE_SITE")

#observables keywords
reaction_data_output_ = Keyword("REACTION_DATA_OUTPUT")
step_ = Keyword("STEP")
count_ = Keyword("COUNT")

#misc
number = Word(nums)
integer = Combine(Optional(plusorminus) + number)
real = Combine(integer +
               Optional(point + Optional(number)) +
               Optional(e + integer))
numarg = (real | integer)
identifier = Word(alphas, alphanums + "_")
dotidentifier = Word(alphas, alphanums + "_" + ".")
bracketidentifier = identifier + lbracket + Word(alphas) + rbracket
statement = Group(identifier + equal + (quotedString | restOfLine))


#math
mathElements = (numarg |   ',' |  '+' | '-' | '*' | '/' | '^' | '&' | '>' | '<' | '=' | '|' ) + Optional(identifier)
nestedMathDefinition     = nestedExpr( '(', ')', content=mathElements)
mathDefinition = OneOrMore(mathElements)


section_enclosure2_ = nestedExpr( '{', '}')


section_enclosure_ = Forward()
nestedBrackets = nestedExpr('[', ']', content=section_enclosure_) 
nestedCurlies = nestedExpr('{', '}', content=section_enclosure_) 
section_enclosure_ << (statement | Group(identifier + ZeroOrMore(identifier) + nestedCurlies) |  Group(identifier + '@' + restOfLine) | Word(alphas, alphanums + "_[]") | identifier | Suppress(',') | '@' | real)


name = Word(alphanums + '_') 
species = Suppress('()') + Optional(Suppress('@' + Word(alphanums + '_-'))) + ZeroOrMore(Suppress('+') + Word(alphanums + "_" + ":#-")
                                    + Suppress("()") + Optional(Suppress('@' + Word(alphanums + '_-'))))

# bng pattern definition
component_definition = Group(identifier.setResultsName('componentName') + Optional(Group(tilde + delimitedList(identifier|integer,delim='~')).setResultsName('state')))
component_statement = Group(identifier.setResultsName('componentName') + Optional(Group(Suppress(bang) + (numarg | '+' | '?')).setResultsName('bond')) + \
                      Optional(Group(Suppress(tilde)+ (identifier | integer)).setResultsName('state')))

molecule_definition = Group(identifier.setResultsName('moleculeName') +
                            Optional((lparen + delimitedList(component_definition, delim=',').setResultsName('components') + rparen)) +
                            Optional(Group('@' + Word(alphanums + '_-')).setResultsName('moleculeCompartment')))
molecule_instance = Group(identifier.setResultsName('moleculeName') +
                          Optional((lparen + delimitedList(component_statement, delim=',').setResultsName('components') + rparen)) +
                          Optional(Group('@' + Word(alphanums + '_-')).setResultsName('moleculeCompartment')))
species_definition = Group(Optional(Group('@' + Word(alphanums + '_')).setResultsName('speciesCompartment') + Suppress('::')) +
                           delimitedList(molecule_instance, delim='.').setResultsName('speciesPattern'))
reaction_definition = Group(Group(delimitedList(species_definition, delim='+')).setResultsName('reactants') + (uni_arrow | bi_arrow) +
                            Group(delimitedList(species_definition, delim='+')).setResultsName('products') + 
                            Group(lbracket + (numarg | identifier) + Optional(comma + (numarg| identifier)) + rbracket).setResultsName('rate'))

# generic hash section grammar
hashed_section = (hashsymbol + Group(OneOrMore(name) + section_enclosure2_))

# hash molecule_entry
molecule_entry = Group(molecule_definition + Optional(Group(lbrace + ZeroOrMore(statement) + rbrace)))
hashed_molecule_section = Group(hashsymbol + Suppress(define_molecules_) + lbrace + OneOrMore(molecule_entry) + rbrace)

# hash reaction entry
hashed_reaction_section = Group(hashsymbol + Suppress(define_reactions_) + lbrace + OneOrMore(reaction_definition) + rbrace)

# hash observable entry
count_definition = Group(count_ + lbracket + species_definition.setResultsName('speciesPattern') + Suppress(',') + identifier + rbracket)
observable_entry = Group(lbrace + Group(delimitedList(count_definition, delim='+')).setResultsName('patterns') + rbrace + Suppress('=>') + quotedString.setResultsName('outputfile'))
hashed_observable_section = Group(hashsymbol + Suppress(reaction_data_output_) + lbrace + OneOrMore(observable_entry | statement) + rbrace)

# hash initialization entry
key = identifier + Suppress('=')
value = restOfLine
release_site_definition = Group(identifier.setResultsName('name') + release_site_ + lbrace + dictOf(key,value).setResultsName('entries') + rbrace)
object_definition = Group(identifier.setResultsName('compartmentName') + Suppress(object_) + (bracketidentifier | identifier) + (nestedExpr('{', '}',content=statement)).setResultsName('compartmentOptions'))
hashed_initialization_section = Group(hashsymbol + Suppress(instantiate_) + identifier.setResultsName('name') +
                                identifier.setResultsName('type') + lbrace + Group(ZeroOrMore(release_site_definition | object_definition)).setResultsName('entries') + rbrace )

other_sections = section_enclosure_
#statement = Group(identifier + equal + (quotedString | OneOrMore(mathElements)))  + Suppress(LineEnd() | StringEnd())
grammar = ZeroOrMore(Suppress(other_sections) | Suppress(statement) | hashed_molecule_section.setResultsName('molecules') | hashed_reaction_section.setResultsName('reactions') | 
                     hashed_observable_section.setResultsName('observables') | hashed_initialization_section.setResultsName('initialization') | Suppress(hashed_section))

nonhashedgrammar = ZeroOrMore(Suppress(statement) | Suppress(hashed_section) | Dict(other_sections))


statementGrammar = ZeroOrMore(statement | Suppress(other_sections) | Suppress(hashed_section))

singleLineComment = "//" + restOfLine
grammar.ignore(singleLineComment)
grammar.ignore(cppStyleComment)
nonhashedgrammar.ignore(singleLineComment)
nonhashedgrammar.ignore(cppStyleComment)

statementGrammar.ignore(singleLineComment)
statementGrammar.ignore(cppStyleComment)

