import grammarDefinition as g

if __name__ == "__main__":
    s= g.hashed_observable_section.parseString('''#REACTION_DATA_OUTPUT
{
   STEP = 1e-6
    Species    Clusters  R(l!0).L(r!0,r!1).R(l!1)  // Any species with crosslinked receptors
    Molecules  LRmotif   L(r!0).R(l!0)
    Molecules  Lfreesite L(r)
    Molecules  Rfreesite R(l)
    Species    Lmonomer  L(r,r,r)
    Species    Rmonomer  R(l,l)
    Molecules  Ltot      L()    
    Molecules  Rtot      R() 
}
''')
    print s
