# /usr/bin/env python
# -*- coding:utf-8 -*-

'''
Created on 12 oct. 2012

@author: Pyke75, benjello
'''

from __future__ import division 
from src.lib.simulation import Simulation
from src.lib.simulation import ScenarioSimulation
from src.lib.utils import of_import

from pandas import DataFrame, concat
from rent import get_loyer


from datetime import datetime    

# TODO check the statmarit, quimen, quifam add check consistency


def total_pension(rev_non_custodian, nb_enf, temps_garde = "classique"):
    """
    Sets total pension according to the French Ministry of justice table
    
    Parameters
    ----------
    rev_non_custodian : float
                        Revenue of the non-custodian parent
    nb_enf : integer
             number of children member of the custodian parent household
    temps_garde : amplitude du droit de visite
    
    Returns
    -------
    """

    min_vital_mensuel = 475

    coef = {'1': .18,
            '2': .31,
            '3': .40, 
            '4': .47,
            '5': .53,
            '6': .57}
    

    rev_net = max((rev_non_custodian - 12*min_vital_mensuel),0)

    if temps_garde == "classique":
        pension = rev_net*coef[str(nb_enf)]*.75 # TODO arrondi au .5 point de pourcentage à faire
        
    elif temps_garde == "reduite":
        pension = rev_net*coef[str(nb_enf)]
        
    elif temps_garde == "alternee_pension_non_decl":
        pension = rev_net*coef[str(nb_enf)]/2
        
    elif temps_garde == "alternee_pension_decl":
        pension = rev_net*coef[str(nb_enf)]/2
    
    return pension


def _uc_couple(age, only_kids = False):
    """
    Compute the consuption units using the INSEE scale for couples
     
    Parameters
    ----------
    age : list
    only_kids: bool
    """
    uc_adt = 0.5
    uc_enf = 0.3
    uc = .5
    if only_kids:
        uc = 0
    
    for ag in age:        
        adt = ( (15 <= ag) & (ag <= 150))
        enf = (0  <= ag) & (ag <= 14)
        uc += adt*uc_adt + enf*uc_enf
    
    return uc - only_kids*uc_adt*2
        
    
def _uc_nc(age, alt = False, only_kids = False, alpha = 0, beta = .5):
    """
    Compute the consuption units using the INSEE scale for the non custodian parent
     
    Parameters
    ----------
    alpha : float
            likely < 1, factor multiplying the chidlren uc for the non_custodian parent
    beta  : float
            factor multiplying the children uc for alternate custody    
    """
    if not alt:
        uc_adt = 0.5*alpha
        uc_enf = 0.3*alpha
    else:
        uc_adt = 0.5*beta
        uc_enf = 0.3*beta
    
    uc = 1
    if only_kids:
        uc = 0
        
    for ag in age:        
        adt = ( (15 <= ag) & (ag <= 150))
        enf = (0  <= ag) & (ag <= 14)
        uc += adt*uc_adt + enf*uc_enf
    
    return uc - uc_adt
    
def _uc_c(age, alt = False , only_kids = False, gamma = 1, beta = .5):
    """
    Compute the consuption units using the INSEE scale for the custodian parent
     
    Parameters
    ----------
    beta  : float
            factor multiplying the children uc for alternate custody 
        
    gamma : float
            factor multiplying the children uc for single parent household
    """

    if not alt:
        uc_adt = 0.5*gamma
        uc_enf = 0.3*gamma
    else:
        uc_adt = 0.5*beta
        uc_enf = 0.3*beta

    
    uc = 1
    if only_kids:
        uc = 0
        
    for ag in age:        
        adt = ( (15 <= ag) & (ag <= 150))
        enf = (0  <= ag) & (ag <= 14)
        uc += adt*uc_adt + enf*uc_enf
    
    return uc - uc_adt


class DesunionSimulation(Simulation):
    """
    A simulation class for a couple that will get separated 
    """
    def __init__(self):
        super(DesunionSimulation, self).__init__()

        # TODO: changer les noms part et chef
        self.scenario = None
        self.scenario_seuls = None
        self.scenario_chef = None # scenario_chef est donc un attribut de la classe DesunionSimulation
        self.scenario_part = None # idem
        self.scenario_chef_seul = None
        self.scenario_part_seul = None
        self.decomp_file = None

        self.pension_alimentaire = None
        self.children = dict() # {noi: {'non_custodian': None, 'temps_garde': None, 'pension_alim': None}
        # du point de vue du parent non gardien
        # garde_classique
        # garde_alternée
        # garde_réduite

        self.uc = dict()
        
        self.nmen = None
        self.maxrev = None
        self.uc_parameters = dict(alpha = 0, beta = .5, gamma = 1) # TODO: define here alpha etc
        self.disabled_prestations = None
    
    def set_uc_parameters(self, parameters):
        """
        Set the standard of living parameters
        """
        for key, val in parameters.iteritems():
            self.uc_parameters[key] = val
        
    def set_config(self, **kwargs):
        """
        Configures the ScenarioSimulation
        
        Parameters
        ----------
        scenario : a Scenario instance. By default, None selects Scenario()
        country  : a string containing the name of the country
        param_file : the socio-fiscal parameters file
        totaux_file : the totaux file
        xaxis : the revenue category along which revenue varies
        maxrev : the maximal value of the revenue
        nmen : the number of different households
        same_rev_couple : divide the revenue equally between the two partners
        mode : 'bareme' or 'castype' TODO: change this 
        """
        
        specific_kwargs = self._set_config(**kwargs)
        self.Scenario = of_import('utils', 'Scenario', country = self.country)
        
        if self.scenario is None:
            try:                
                self.scenario = kwargs['scenario']
            except:
                self.scenario = self.Scenario()
                self.scenario_seuls = self.Scenario()
                
        self.scenario.year = self.datesim.year
        self.scenario_seuls.year = self.datesim.year
        
        for key, val in specific_kwargs.iteritems(): 
            if hasattr(self, key):
                setattr(self, key, val)
        
        

    def break_union(self, housing_custodian = None, housing_non_custodian = None):
        """
        Break union
        
        Parameters
        ----------
        
        housing_custodian     : dict
                             housing parameters for the custodian parent
        housing_non_custodian : dict
                             housing parameters for the non-custodian parent
        """

        scenario = self.scenario
        scenario_chef = self.Scenario()
        scenario_part = self.Scenario()
        scenario_chef_seul = self.Scenario()
        scenario_part_seul = self.Scenario()
        
        scenario_chef.year = self.datesim.year

        for scenar in [ self.scenario_seuls, scenario_chef, scenario_part, 
                         scenario_chef_seul, scenario_part_seul ]:
            scenar.year = self.datesim.year
            scenar.nmen = 1


        sal_chef = scenario.indiv[0]['sali']   # TODO: Should be more general

        scenario_chef.indiv[0].update({'sali': sal_chef })
        scenario_chef_seul.indiv[0].update({'sali': sal_chef })
        for variable in ["ppe_tp_sa", "ppe_du_sa"]:
            scenario_chef.indiv[0].update({variable: scenario.indiv[0][variable] })
            scenario_chef_seul.indiv[0].update({variable: scenario.indiv[0][variable] })

        sal_part = scenario.indiv[1]['sali']   # Could be more general
        scenario_part.indiv[0].update({'sali': sal_part })
        scenario_part_seul.indiv[0].update({'sali': sal_part })

        for variable in ["ppe_tp_sa", "ppe_du_sa"]:
            scenario_chef.indiv[0].update({variable: scenario.indiv[0][variable] })
            scenario_chef_seul.indiv[0].update({variable: scenario.indiv[0][variable] })
            scenario_part.indiv[0].update({variable: scenario.indiv[1][variable] })
            scenario_part_seul.indiv[0].update({variable: scenario.indiv[1][variable] })

        # TODO: get more infos from couple scenario

        noi_enf_part = 1 
        noi_enf_chef = 1
        alv_chef = 0
        alv_part = 0
        alr_chef = 0
        alr_part = 0
        
        for noi, val in self.children.iteritems(): 

            non_custodian = val['non_custodian']
            temps_garde = val['temps_garde']
            pension_alim = val['pension_alim']
            birth = scenario.indiv[noi]['birth']
            
            if temps_garde in ['classique', 'reduite']:

                if non_custodian == 'chef':
                    scenario_part.addIndiv(noi_enf_part, birth, 'pac', 'enf')
                    scenario_part.indiv[noi_enf_part].update({'quimen': 'enf'+str(noi_enf_part)})
                    noi_enf_part += 1
                    alv_chef += pension_alim
                    alr_part += pension_alim
                    scenario_part.declar[0]['caseT'] = True
                elif non_custodian == 'part':
                    scenario_chef.addIndiv(noi_enf_chef, birth, 'pac', 'enf') 
                    scenario_chef.indiv[noi_enf_part].update({'quimen': 'enf'+str(noi_enf_part)})
                    noi_enf_chef += 1
                    alv_part += pension_alim
                    alr_chef += pension_alim
                    scenario_chef.declar[0]['caseT'] = True
               
            elif temps_garde == 'alternee_pension_non_decl':# garde alternée fiscale = pas de pension alimentaire déclarée aux impots mais partage du QF
                scenario_part.addIndiv(noi_enf_part, birth, 'pac', 'enf')
                scenario_part.indiv[noi_enf_part].update({'alt': 1, 'quimen': 'enf'+str(noi_enf_part)})
                scenario_part.declar[0]['caseT'] = True
                noi_enf_part += 1

                scenario_chef.addIndiv(noi_enf_chef, birth, 'pac', 'enf')
                scenario_chef.indiv[noi_enf_chef].update({'alt': 1})
                scenario_chef.declar[0]['caseT'] = True
                noi_enf_chef += 1

                
            elif temps_garde == 'alternee_pension_decl':# TODO: garde alternée pas de pension alimentaire ?
                                            # garde alternée juridique ou pas

                if non_custodian == 'chef':
                    scenario_part.addIndiv(noi_enf_part, birth, 'pac', 'enf')
                    scenario_part.declar[0]['caseT'] = True
                    noi_enf_part += 1
                    alv_chef += pension_alim
                    alr_part += pension_alim
                elif non_custodian == 'part':
                    scenario_chef.addIndiv(noi_enf_chef, birth, 'pac', 'enf') 
                    scenario_chef.declar[0]['caseT'] = True
                    noi_enf_chef += 1
                    alv_part += pension_alim
                    alr_chef += pension_alim 
                    
            else:
                raise Exception('break_union: Error somewhere')
                
        # Updating pension alimentaire
        # Beware : received pension alim. are attributed for individuals
        #          paid pension alim. are "charges déductibes" on foyers' declarations  
        alv_net_chef = alv_chef - alr_chef
        if alv_net_chef >= 0:   
            scenario_chef.declar[0].update({'f6gu': alv_net_chef}) # TODO: pas forcément en 6gu 
            scenario_part.indiv[0].update({'alr': alv_net_chef})
        else:
            scenario_chef.indiv[0].update({'alr': -alv_net_chef})
            scenario_part.declar[0].update({'f6gu': -alv_net_chef})

        self.scenario_chef = scenario_chef
        self.scenario_part = scenario_part

        self.scenario_chef_seul = scenario_chef_seul
        self.scenario_part_seul = scenario_part_seul

        # Updating households
        
        pension_alim_tot = sum([ var['pension_alim'] for var in self.children.values()])


        for scenar in [ self.scenario, self.scenario_seuls, scenario_chef, scenario_part, 
                         scenario_chef_seul, scenario_part_seul ]:
            scenar.genNbEnf()

        if housing_non_custodian is None:
            housing_non_custodian = {'loyer': get_loyer(scenario_chef)}
            housing_non_custodian_seul = {'loyer': get_loyer(scenario_chef_seul) }

        for key, val in housing_non_custodian.iteritems():
            scenario_chef.menage[0].update({key: val}) 

        for key, val in housing_non_custodian_seul.iteritems():
            scenario_chef_seul.menage[0].update({key: val})


        if housing_custodian is None:
            housing_custodian = {'loyer': get_loyer(scenario_part)}
            housing_custodian_seul = {'loyer': get_loyer(scenario_part_seul)}

        for key, val in housing_custodian.iteritems():
            scenario_part.menage[0].update({key: val})
            
        for key, val in housing_custodian_seul.iteritems():
            scenario_part_seul.menage[0].update({key: val})
        
        
    def set_children(self, children):
        """
        Sets the children involved
        
        Parameters
        ----------
        children:   dict of dict of the following form 
                    {'MyName': {'birth': "2000-01-01", 'non_custodian' : 'chef', 
                    'temps_garde': 'classique', 'pension_alim' : 1000}}
         
        """ 
        noi = 2
        for name, vars_dict in children.iteritems():
            self.children[noi] = vars_dict
            self.children[noi]['birth'] =  datetime.strptime(children[name]['birth'] ,"%Y-%m-%d").date()
            noi += 1
         

    def create_couple(self, sal_chef, sal_part, housing = None):
        '''
        Creates the united couples with and without children
        
        Parameters
        ----------
        sal_chef : float
                   Salary of the non custodian parent
        sal_part : float
                   Salary of the custodian parent
        '''
         
        scenario = self.scenario
        scenario_seuls = self.scenario_seuls
        
        scenario.addIndiv(1, datetime.strptime("1975-01-01" ,"%Y-%m-%d").date(), "conj", "part")
        scenario_seuls.addIndiv(1, datetime.strptime("1975-01-01" ,"%Y-%m-%d").date(), "conj", "part")
            
        for noi, child in self.children.iteritems():
            scenario.addIndiv(noi, child['birth'], "pac", "enf" )  
        
        scenario.indiv[0].update({ 'sali': sal_chef })
        scenario_seuls.indiv[0].update({ 'sali': sal_chef })
        if sal_chef >= 1072*12:  # TODO: for 2011
            scenario.indiv[0].update({"ppe_tp_sa":True})
            scenario_seuls.indiv[0].update({"ppe_tp_sa":True})
        else:
            duree = round(1607*sal_chef/(1072*12))
            scenario.indiv[0].update({"ppe_du_sa": duree })   # 1607h fonction publique
            scenario_seuls.indiv[0].update({"ppe_du_sa": duree})
        
        scenario.indiv[1].update({ 'sali': sal_part})
        scenario_seuls.indiv[1].update({ 'sali': sal_part})
        if sal_part >= 1072*12:  # TODO: for 2011
            scenario.indiv[1].update({"ppe_tp_sa":True})
            scenario_seuls.indiv[1].update({"ppe_tp_sa":True})
        else:
            duree = round(1607*sal_part/(1072*12))
            scenario.indiv[1].update({"ppe_du_sa": duree })   # 1607h fonction publique
            scenario_seuls.indiv[1].update({"ppe_du_sa": duree})
        
        if housing is None:
            scenario.menage[0].update({'loyer' : get_loyer(scenario)})
            scenario_seuls.menage[0].update({'loyer' : get_loyer(scenario_seuls)})
        else:
            for key, val in housing.iteritems:
                scenario.menage[0].update({key: val})
                scenario_seuls.menage[0].update({key: val})
        
        
    def _compute(self):
        """
        Computes data_dict  from scenari
        """
        scenari = { 'couple' : self.scenario,
                   'couple_seul' : self.scenario_seuls, 
                    'chef'   : self.scenario_chef,
                    'part'   : self.scenario_part,
                    'chef_seul'  : self.scenario_chef_seul,
                    'part_seul' : self.scenario_part_seul}
        datas = dict()

        for name, scenario in scenari.iteritems():
            simu = ScenarioSimulation()
            simu.set_config(year = self.datesim.year, scenario = scenario, 
                            country = self.country,
                            decomp_file = self.decomp_file, 
                            nmen = self.nmen,
                            maxrev = self.maxrev)
            simu.set_param(self.P, self.P_default)
            simu.disable_prestations(self.disabled_prestations)
            
            data, data_default = simu.compute()
            datas[name] = {'data' : data, 'default': data_default}
        return datas
    
    def _compute_uc(self):
        """
        Compute uc for every household
        """
        
        alpha = self.uc_parameters['alpha']
        beta = self.uc_parameters['beta']
        gamma = self.uc_parameters['gamma']
        self.uc = dict()
        scenari = { 'couple' : self.scenario, 
                    'couple_seul' : self.scenario_seuls,
                    'chef'   : self.scenario_chef, 
                    'part'   : self.scenario_part,
                    'chef_seul' : self.scenario_chef_seul,
                    'part_seul' : self.scenario_part_seul
                    }

        alt = (self.get_temps_garde() in ['alternee_pension_decl', 'alternee_pension_non_decl'])

        for name, scenario in scenari.iteritems():
            age = dict()
            for noi, var in scenario.indiv.iteritems():   
                age[noi] = int((self.datesim - var['birth']).days/365.25)
            
            if name in ['couple', 'couple_seul']:
                self.uc[name] = _uc_couple(age.values())
            
            elif name in ['chef_seul', 'part_seul']:
                self.uc[name] = _uc_c(age.values())
            
            elif name == 'chef':
                if (self.get_temps_garde() not in ['alternee_pension_non_decl']): # When children are missing in scenario_chef
                    for var in self.children.values():
                        noi = noi + 1
                        age[noi] = int((self.datesim - var['birth']).days/365.25)
                                    
                self.uc[name] =  _uc_nc(age.values(), alt=alt, only_kids=False, alpha=alpha, beta=beta)
            
            elif name == 'part':
                self.uc[name] =  _uc_c(age.values(), alt=alt, only_kids=False, gamma=gamma, beta=beta)
            
    
    def get_temps_garde(self):
        """
        Retruns temps_garde
        """    
        noi = self.children.keys()[0]
        return self.children[noi]['temps_garde']
        
        
        
    def get_results_dataframe(self, default = False, index_by_code = False):
        '''
        Formats data into a dataframe
        '''
        datas = self._compute()
        self._compute_uc()
        uc = self.uc
        dfs = dict()

        for scenario, dico in datas.iteritems():
            data = dico['data']
            data_default = dico['default']

            data_dict = dict()
            index = []
            
            if default is True:
                data = data_default
            
            for row in data:
                if not row.desc in ('root'):
                    if row.code == 'revdisp':
                        revdisp = row.vals
                    if index_by_code is True:
                        index.append(row.code)
                        data_dict[row.code] = row.vals
                    else:
                        index.append(row.desc)
                        data_dict[row.desc] = row.vals
            
            df = DataFrame(data_dict).T
            
            df = df.reindex(index)
            df = df.rename(columns = {0: scenario})
            nivvie = revdisp/uc[scenario] # TODO: include savings !!
            df = concat([df, 
                         DataFrame({scenario: nivvie}, index=['nivvie'])
                         ])
            dfs[scenario] = df
            
        
        first = True

        for df in dfs.itervalues():
            if first:
                df_final = df
                first = False
            else:
                df_final = concat([df_final, df], axis=1, join ="inner")
        
        return df_final
    
    
    def set_pension(self, pension = None):
        """
        Sets pension according to Ministry of Justice
        """
        rev_non_custodian = self.scenario.indiv[0]['sali']
        nb_enf = len(self.children)
        noi = self.children.keys()[0]
        temps_garde = self.children[noi]['temps_garde']
        
        if temps_garde == "alternee_pension_non_decl":
            self.disable_prestations(['asf'])   # We disable asf because it is on when "fiscal" pension is zero
        
        if pension is None:
            pension_per_child = total_pension(rev_non_custodian, 
                                                 nb_enf, 
                                                 temps_garde=temps_garde)/nb_enf
        else:
            pension_per_child = pension/nb_enf
            
        for child in self.children.itervalues():
            child['pension_alim'] = pension_per_child
    

    def diag(self):

        df = self.get_results_dataframe(index_by_code = True)
        df_nivvie = df.xs('nivvie')
        df_revdisp = df.xs('revdisp')
        df_rev = df.xs('rev_trav') + df.xs('pen') + df.xs('rev_cap_net') 
        
        df_af = df.xs('af')

        df_pfam = df.xs('pfam') 
        df_mini = df.xs('mini')
        df_logt = df.xs('logt')
        df_impo = df.xs('ppe') + df.xs('impo')
        df_impo.name = "impo+ppe"
        df_public = df.xs('psoc') + df.xs('ppe') + df.xs('impo')
        
        loyer_chef = self.scenario_chef_seul.menage[0]['loyer']
        
        pension_alim_tot = sum([ var['pension_alim'] for var in self.children.values()])
        
        noi = self.children.keys()[0]
        if self.children[noi]["temps_garde"] == 'alternee_pension_non_decl':
            
            df_revdisp['chef'] = ( df_rev['chef'] + df_mini['chef_seul'] + 
                                   df_af['part']/2 + 
                                   df_logt['chef_seul'] - pension_alim_tot +
                                   df_impo['chef'] )
            df_pfam['chef'] = df_af['part']/2
            df_logt['chef'] = df_logt['chef_seul']
            df_mini['chef']  = df_mini['chef_seul']
            df_public['chef'] = ( df_logt['chef_seul'] + df_mini['chef_seul']+ 
                                  df_pfam['chef'] + df_impo['chef'] )
            df_nivvie['chef'] = df_revdisp['chef']/self.uc['chef']
            
            df_revdisp['part'] = ( df_revdisp['part'] - df_af['part']/2 + 
                                   pension_alim_tot )
            df_pfam['part'] -= df_af['part']/2
            df_public['part'] = ( df_logt['part'] + df_mini['part']+ 
                                  df_pfam['part'] + df_impo['part'] )
            df_nivvie['part'] = df_revdisp['part']/self.uc['part'] 
        
        uc_couple = self.uc['couple']
        total_cost_before = ((uc_couple-1.5)/uc_couple)*(df_revdisp['couple'])
        
        public_cost_before = ( df_public['couple'] - df_public['couple_seul'])
        private_cost_before = total_cost_before - public_cost_before
        
        uc_chef = self.uc['chef']
        uc_part = self.uc['part']
        
        total_cost_after_chef = (uc_chef-1)/(uc_chef)*df_revdisp['chef']
        total_cost_after_part = (uc_part-1)/(uc_part)*df_revdisp['part'] 
        
#        total_cost_after = total_cost_after_chef + total_cost_after_part
        
        public_cost_after_chef = df_public['chef'] - df_public['chef_seul']
        public_cost_after_part = df_public['part'] - df_public['part_seul'] 
        
        #public_cost_after = ( public_cost_after_chef + public_cost_after_part )
        #private_cost_after = total_cost_after - public_cost_after
        # private_cost_after_chef = total_cost_after_chef + pension_alim_tot - public_cost_after_chef
        # private_cost_after_part = total_cost_after_part - pension_alim_tot - public_cost_after_part

        private_cost_after_chef = total_cost_after_chef - public_cost_after_chef
        private_cost_after_part = total_cost_after_part - public_cost_after_part
        
        desunion_public_cost = df_public['part'] + df_public['chef'] - df_public['couple'] 
        
        nivvie_loss_couple = df_nivvie[u"couple"]/df_nivvie["couple_seul"] 
        nivvie_loss_chef = df_nivvie[u"chef"]/df_nivvie["chef_seul"]
        nivvie_loss_part = df_nivvie[u"part"]/df_nivvie["part_seul"]
        
        
        df2 = DataFrame( [df_revdisp, df_pfam, df_mini, df_logt, df_impo, df_nivvie])
        df2 = df2[ ['couple', 'part', 'chef'] ]
        df2 = df2.set_value(u"dépense totale pour enfants", 'couple', total_cost_before)
        df2 = df2.set_value(u"dépense totale pour enfants", 'chef', total_cost_after_chef)
        df2 = df2.set_value(u"dépense totale pour enfants", 'part', total_cost_after_part)
        df2 = df2.set_value(u"prise en charge publique de l'enfant", 'couple', public_cost_before)
        df2 = df2.set_value(u"prise en charge publique de l'enfant", 'chef', public_cost_after_chef)
        df2 = df2.set_value(u"prise en charge publique de l'enfant", 'part', public_cost_after_part)
        df2 = df2.set_value(u"prise en charge privée de l'enfant", 'couple', private_cost_before)
        df2 = df2.set_value(u"prise en charge privée de l'enfant", 'chef', private_cost_after_chef)
        df2 = df2.set_value(u"prise en charge privée de l'enfant", 'part', private_cost_after_part)
        df2 = df2.set_value(u"loyer", 'couple', 12*self.scenario.menage[0]['loyer'])    
        df2 = df2.set_value(u"loyer", 'chef', 12*loyer_chef)
        df2 = df2.set_value(u"loyer", 'part', 12*self.scenario_part.menage[0]['loyer'])
        df2 = df2.set_value(u"pension", 'couple', 0)    
        df2 = df2.set_value(u"pension", 'chef', -pension_alim_tot )
        df2 = df2.set_value(u"pension", 'part', pension_alim_tot)
        
        df2 = df2.set_value(u"nivvie_loss", 'couple', nivvie_loss_couple)    
        df2 = df2.set_value(u"nivvie_loss", 'chef', nivvie_loss_chef)
        df2 = df2.set_value(u"nivvie_loss", 'part', nivvie_loss_part)
        df2 = df2.set_value(u"coût public de la désunion", "couple", desunion_public_cost )
        
        df2 = df2.T
        df2.index.name = u"ménage"
        df2 = df2.reset_index() 
        
        return df2


if __name__ == '__main__':
    
    parent = "non_custodian"
    
    age_c = [30, 30,  10, 10]
    age = [30,  10, 10]
    alt = False
    alpha = 1 
    beta  = .5
    gamma = 1.5
    print _uc_couple(age_c, only_kids = False)
    print _uc_c(age, alt, only_kids = False, gamma = gamma , beta = beta)    print _uc_nc(age, alt, only_kids = False, alpha = alpha, beta = beta)