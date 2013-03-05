# /usr/bin/env python-
# -*- coding:utf-8 -*-

from __future__ import division

'''
Created on 28 févr. 2013

Barème Unaf

@author: MBJ et PYC
'''
"""
Using families from:
  http://www.unaf.fr/spip.php?rubrique160   
"""


import numpy as np
from pandas import DataFrame


def get_unaf(d, f, a=0, b=0, c=0, e=0, g=0):
    """
    Cost of childrens according to an equation based on UNAF budget type
    """
    if g == 0:
        g = (d+f)/2
    cost =  12*(1294.952564*a + 1942.428846*b + 337.639231*c + 427.795449*d +
        471.730000*e + 668.460897*f + 140.496538*g)
    return cost

def test():
    # a : adulte isolé
    # b : couple
    # c : enfant dans couple
    # d : enfan isolé
    # e : ado couple
    # f : ado isolé 
    # g : chambre d'enfant
    
    # A: 2a,2e 
    #  b + 2*c + g     
    fa = [0,1,2,0,0,0,1]
    ma =  2754.74     
    
    # B : 2a,2ea,supp: 
    #  b + 2*e + 2*g
    fb = [0,1,0,0,2,0,2] 
    mb = 3165.15
      
    # C : 1a,2e:   
    #  a + 2*d + g
    fc = [1,0,0,2,0,0,1]
    mc = 2291.04     
    
    # D: 2a, 2e, 2ea, 2*supp :       
    #   b + 2*c + 2*e + 3*g
    fd = [0,1,2,0,2,0,3]  
    md = 3969.81
    
    #E : 2a,1ea
    #    b + e + g 
    fe = [0,1,0,0,1,0,1] 
    me = 2549.17     
    
    #F : 2a, 1e, 2ea   
    #    b + c + 2*e + 2*g 
    ff = [0,1,1,0,2,0,2]
    mf =  3514.12                                              
    
    #G: 2a, 1e ,1ea, supp
    #   b + c + e + 2*g 
    fg = [0,1,1,0,1,0,2]
    mg =  3042.39
    
    #H: 1a, 1ea
    #    a + f + g
    fh = [1,0,0,0,0,1,1]
    mh =  2103.91
    
    # solve f*x = m
    
    # A supplementary equation is needed because the system is inconsistant
    fsup = [1,-1/1.5,0,0,0,0,0]
    msup = 0
    f = [fa, fb , fc, fd, fe, ff, fg, fh, fsup]
    m = [ma, mb , mc, md, me, mf, mg, mh, msup]
    
    results = DataFrame()
    
    for i in range(8):
        selected_f1 = list(f)
        selected_m1 = list(m)
        selected_f1.pop(i)
        selected_m1.pop(i)
        for j in range(7):
            selected_f = list(selected_f1)
            selected_m = list(selected_m1)
            selected_f.pop(j)
            selected_m.pop(j)

            f_mat = np.array(selected_f)
    
            m_vec = np.array(selected_m)          
    
            # print i, np.linalg.det(f_mat)
            try: 
                x = DataFrame({str(i)+str(j): np.linalg.solve(f_mat, m_vec)}).T
            except:
                
                x = None
                
            from pandas import concat
            if x is not None:
                results = concat([results,x])
                
    print results
    print results.mean()
    print results.std()
    print results.std()/results.mean()

if __name__ == '__main__':
    test()