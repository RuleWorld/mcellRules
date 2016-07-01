from pyparsing import *

identifier = Word(alphas, alphanums + "_")
plusorminus = Literal('+') | Literal('-')
point = Literal('.')
equal = Suppress("=")
statement = Group(identifier + equal + (quotedString | restOfLine))
e = CaselessLiteral('E')
number = Word(nums)
integer = Combine(Optional(plusorminus) + number)
real = Combine(integer +
               Optional(point + Optional(number)) +
               Optional(e + integer))

section_enclosure_ = Forward()
nestedParens = nestedExpr('(', ')', content=section_enclosure_) 
nestedBrackets = nestedExpr('[', ']', content=section_enclosure_) 
nestedCurlies = nestedExpr('{', '}', content=section_enclosure_) 
section_enclosure_ << (statement | Group(identifier + ZeroOrMore(identifier) + nestedCurlies) |  Group(identifier + '@' + restOfLine) | Word(alphas, alphanums + "_[]") | identifier | Suppress(',') | '@' | real)



data = '''
VIZ_OUTPUT {
   MODE = CELLBLENDER
   FILENAME = "./viz_data/rec_dim"
   MOLECULES
   {
      NAME_LIST {ALL_MOLECULES}
      ITERATION_NUMBERS {
      ALL_DATA @ [1, 100, [200 TO 100000 STEP 100]]
      }
   }
} '''


print section_enclosure_.parseString(data)