# -*- coding:utf-8 -*-
# Created on 10 janv. 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


def uc(a = 1, e=0, ea=0, alpha=0, e_ng=0):
    # unités de consommation du ménage
    # a  : nombre d'adultes
    # ea : nombre d'enfants de plus de 14 ans, assimilés à des adultes
    # e  : nombre d'enfants
    a = a + ea
    monop = (a==1)
    return (1 + .5*(a-1) + .3*(e + alpha*e_ng)*( 1*(!nomonp) + gamma*monop )   )

def cenf(a = 1, e=0, ea=0, alpha=0, e_ng=0):
    # Coût des enfants (en proportion du revenu du ménage)
    # a  : nombre d'adultes
    # ea : nombre d'enfants de plus de 14 ans, assimilés à des adultes
    # e  : nombre d'enfants
    return( ( uc(a, e, ea, alpha, e_ng) - uc(a) )/uc(a, e, ea, alpha, e_ng) )

def cenf_avant_sep(y, e=0, ea=0):
    # Coût des enfants avant séparation (en proportion du revenu du ménage gardien)
    # y  : revenu du ménage non-gardien normalisé par le revenu du ménage gardien
    # a  : nombre d'adultes
    # ea : nombre d'enfants de plus de 14 ans, assimilés à des adultes
    # e  : nombre d'enfants 
    cout = cenf(2,e,ea)*(y+1)
    return(cout)


def pension_alim(y = 1, e=0, ea=0, alpha=0, e_ng=0):
    # Pension alimentaire noramlisé par le revenu du parent gardien hors pension
    # y  : revenu du ménage non-gardien normalisé par le revenu du parent gardien hors pension 
    # a  : nombre d'adultes
    # ea : nombre d'enfants de plus de 14 ans, assimilés à des adultes
    # e  : nombre d'enfants
    p = (uc(1, e, ea) - uc(1, 0, 0, alpha, e_ng))*y/(y*uc(1, 0, 0, alpha, e_ng) + uc(1, e, ea))
    return p



def cenf_apres_sep(y=1, e=0, ea=0, alpha=0, e_ng=0):
    # Coût des enfants après séparation (en proportion du revenu du ménage gardien)
    # y  : revenu du ménage non-gardien normalisé par le revenu du ménage gardien
    # a  : nombre d'adultes
    # ea : nombre d'enfants de plus de 14 ans, assimilés à des adultes
    # e  : nombre d'enfants 
    # p  : pension alimentaire versée par le non-gardien normalisé par le revenu du ménage gardien
    p = pension_alim(y, e, ea, alpha, e_ng)
    cout = cenf(1, e, ea)*(p+1)
    return cout


def cenf_apres_sep_ng(y=1, e=0, ea=0, alpha=0, e_ng=0):
    # Coût des enfants après séparation (en proportion du revenu du ménage gardien)
    # y  : revenu du ménage non-gardien normalisé par le revenu du ménage gardien
    # a  : nombre d'adultes
    # ea : nombre d'enfants de plus de 14 ans, assimilés à des adultes
    # e  : nombre d'enfants 
    # p  : pension alimentaire versée par le non-gardien normalisé par le revenu du ménage gardien
    p = pension_alim(y, e, ea, alpha, e_ng)
    cout = cenf(1, 0, ea, alpha, e_ng)*(y-p)
    return cout

    def nv_couple(y = 1, e=0, ea=0):
        return((1+y)/uc(2, e, ea))


    def nv_gard(y = 1, e=0, ea=0, alpha=0, e_ng=0):
        return((1+pension_alim(y, e, ea, alpha, e_ng))/uc(1, e, ea))
  

    def nv_ngard(y = 1, e=0, ea=0, alpha=0, e_ng=0):
        return( (y-pension_alim(y, e, ea, alpha, e_ng))/uc(1, e, ea, alpha, e_ng))



if __name__ == '__main__':

    print pension_alim(1,1)
    print .3/2.3
    print  cenf_avant_sep(1,1)
    print  pension_alim(1,1)
    print cenf_apres_sep(1,1)
    print cenf_apres_sep_ng(1,1,0,1,1)
