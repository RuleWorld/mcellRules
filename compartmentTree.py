import treelib3

def getCompartmentHierarchy(compartmentList):
    '''
    constructs a tree structure containing the 
    compartment hierarchy excluding 2D compartments
    @param:compartmentList
    '''
    def removeMembranes(tree,nodeID):
        node = tree.get_node(nodeID)
        if node.data == 2:
            parent = tree.get_node(nodeID).bpointer
            if parent == None:
                #accounting for the case where the topmost node is a membrane
                newRoot = tree.get_node(nodeID).fpointer[0]
                tree.root = newRoot
                node = tree.get_node(newRoot)
            else:
                tree.link_past_node(nodeID)
                nodeID = parent
                node = tree.get_node(nodeID)
        for element in node.fpointer:
            removeMembranes(tree,element)
        
    from copy import deepcopy
    tree = treelib3.Tree()
    c2 = deepcopy(compartmentList)
    while len(c2) > 0:
        removeList = []
        for element in c2:
            if c2[element][2] in ['', None]:
                try:
                    tree.create_node(element,element,data=c2[element][0])
                except treelib3.tree.MultipleRootError:
                    #there's more than one top level element
                    tree2 = treelib3.Tree()
                    tree2.create_node('dummyRoot','dummyRoot',data=3)
                    tree2.paste('dummyRoot',tree)
                    tree2.create_node(element,element,parent='dummyRoot',data=c2[element][0])
                    tree = tree2
                removeList.append(element)
            elif tree.contains(c2[element][2]):
                tree.create_node(element,element,parent=c2[element][2],data=c2[element][0])
                removeList.append(element)
        for element in removeList:
            c2.pop(element)
    removeMembranes(tree,tree.root)
    return tree


def getOutsideInsideCompartment(compartmentList,compartment):
    outside = compartmentList[compartment][2]
    for comp in compartmentList:
        if compartmentList[comp][2] == compartment:
            return outside, comp
