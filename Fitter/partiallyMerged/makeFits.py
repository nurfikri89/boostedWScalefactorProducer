#!/usr/bin/env python

import argparse
import ROOT
import sys
import os
import time
import math
import csv
from WTopScalefactorProducer.Fitter.tdrstyle import *
from WTopScalefactorProducer.Fitter.CMS_lumi import *
from WTopScalefactorProducer.Skimmer.getGenEv import getGenEv

from WtaggingFitter import WTaggingFitter

from ROOT import *

parser = argparse.ArgumentParser(description='Fitter')

# --- Global parameters for ROOT style and RooFit 

setTDRStyle()
gStyle.SetOptTitle(0)
#RooMsgService.instance().setGlobalKillBelow(RooFit.FATAL)
#RooMsgService.instance().setSilentMode(True)

# --- Tagging options
parser.add_argument('--tagger', action="store",type=str,dest="tagger",default="SelectedJet_tau21", help="Name of tagger variable (tau32/tau21/ddt)")
parser.add_argument('--massvar', action="store",type=str,dest="massvar",default="SelectedJet_softDrop_mass", help="Name of mass variable to fit")
parser.add_argument('--xtitle', action="store",type=str,dest="xtitle",default="Corrected PUPPI softdrop mass (GeV)", help="x axis title of mass variable to fit")
parser.add_argument('--HP', action="store", type=float,dest="cutHP",default=0.35)
parser.add_argument('--LP', action="store", type=float,dest="cutLP",default=0.75)
parser.add_argument('--minX', action="store", type=float,dest="minX",default=50. , help="Lower mass cut")
parser.add_argument('--maxX', action="store", type=float,dest="maxX",default=130., help="Upper mass cut")
parser.add_argument('--ptmin', action="store", type=float,dest="pTmin",default=200., help="Lower pT cut")
parser.add_argument('--ptmax', action="store", type=float,dest="pTmax",default=10000., help="Upper pT cut")
parser.add_argument('--workspace', action="store",type=str,dest="workspace",default="workspace", help="Name of workspace")
parser.add_argument('--peak', action="store",type=str,dest="peak",default="W", help='Which peak to fit? W / t / Wt')

# --- Personal infile settings
parser.add_argument('--sample', action="store",type=str,dest="sample",default="powheg", help='Which tt sample is used')
parser.add_argument('--treename', action="store",type=str,dest="intree",default="Events", help='name of in tree')

# --- Fitting options
parser.add_argument('--topPt', action='store_true', dest='topPt', default=False, help='Use top pt reweighting')
parser.add_argument('--topGen', action='store_true', dest='topGen', default=False, help='Use alternate top sample with different generator algorithm (aMC@NLO)')
parser.add_argument('--topShower', action='store_true', dest='topShower', default=False, help='Use alternate top sample with different shower algorithm (HERWIG7)')
parser.add_argument('--fitTT', action='store_true', dest='fitTT', default=False, help='Only do ttbar fits')
parser.add_argument('--fitMC', action='store_true', dest='fitMC', default=False, help='Only do MC fits')
parser.add_argument('--doBinned',dest="doBinnedFit", default=False, action="store_true", help="Do binned instead of unbinned fit")

# --- Running options
parser.add_argument('-b', action='store_true', dest='noX', default=False, help='no X11 windows')
parser.add_argument('-c', '--channel',action="store",type=str,dest="channel",default="em", help="Electron,muon or ele+mu channel. For now, em for all") #FIXME
parser.add_argument('--doWS'  ,dest="doWS", default=False, action="store_true", help="Recreate workspace. If NOT set to True (or workspace does not exist), will use workspace as given in options.workspace (workspace.root by default)")
parser.add_argument('-y', '--year', dest="year", type=int, help="The year for which you want to create the workspace. ")
parser.add_argument('--weightvar', dest="weightvar", type=str, default="weight", help="The name of the event weight variable in the tree.")
parser.add_argument('-v', '--verbose', dest="verbose", action='store_true', default=False, help="Print out more messages.")


options = parser.parse_args()

if options.noX: gROOT.SetBatch(True)

#### <refactor> should be deleted (using expermiment specific layer for that)
lumi = 59970.
CMS_lumi.lumi_13TeV = "60.0 fb^{-1}"
CMS_lumi.writeExtraText = 1
CMS_lumi.extraText = "Preliminary"
CMS_lumi.lumi_sqrtS = "13 TeV" # used with iPeriod = 0, e.g. for simulation-only plots (default is an empty string)
iPos = 11
if( iPos==0 ): CMS_lumi.relPosX = 0.12
iPeriod = 4
#### <\refactor>



# --- Functions definitions

#### <refactor> kinda useless as the only thing it does is call another function
def getSF():
    print "Getting W-tagging SF for cut " ,options.tau2tau1cutHP
    boostedW_fitter_sim = WTaggingFitter(options)
#### <\refactor>

def getLegend():
  legend = TLegend(0.6010112,0.7183362,0.8202143,0.919833)
  legend.SetTextSize(0.032)
  legend.SetLineColor(0)
  legend.SetShadowColor(0)
  legend.SetLineStyle(1)
  legend.SetLineWidth(1)
  legend.SetFillColor(0)
  legend.SetFillStyle(0)
  legend.SetMargin(0.35)
  return legend

def getPavetext():
  addInfo = TPaveText(0.7010112,0.3566292,0.7902143,0.4023546,"NDC")
  addInfo.SetFillColor(0)
  addInfo.SetLineColor(0)
  addInfo.SetFillStyle(0)
  addInfo.SetBorderSize(0)
  addInfo.SetTextFont(42)
  addInfo.SetTextSize(0.040)
  addInfo.SetTextAlign(12)
  return addInfo

c1 = TCanvas("test","test",800,800)    
def drawFrameGetChi2(variable,fitResult,dataset,pdfModel,isData):
    
    wpForPlotting ="%.2f"%options.tau2tau1cutHP
    wpForPlotting = wpForPlotting.replace(".","v")
    postfix=""
    title = "PUPPI softdrop jet mass (GeV)"
    
    
    frame = variable.frame()
    if(isData): dataset.plotOn(frame,RooFit.DataError(RooAbsData.Poisson),RooFit.Name(dataset.GetName ()))
    else: dataset.plotOn(frame,RooFit.DataError(RooAbsData.SumW2),RooFit.Name(dataset.GetName ()))
    pdfModel.plotOn(frame,RooFit.VisualizeError(fitResult,1), RooFit.Name("Fit error"),RooFit.FillColor(kGray),RooFit.LineColor(kGray)) #,RooFit.Normalization(1.0,RooAbsReal.RelativeExpected))
    pdfModel.plotOn(frame,RooFit.LineColor(kBlack),RooFit.Name(pdfModel.GetName())) #,RooFit.Normalization(1.0,RooAbsReal.RelativeExpected))
    chi2 = frame.chiSquare(pdfModel.GetName(), dataset.GetName (), -2) #for pass/fail adding the number of observations in  fail/pass (16) minus nFitParam(14) 
    pdfModel.plotOn(frame,RooFit.Name( "Gaussian 2" ),RooFit.Components("gaus2*"),RooFit.LineStyle(kSolid),RooFit.LineColor(kBlue+3),RooFit.Normalization(1.0,RooAbsReal.RelativeExpected))
    pdfModel.plotOn(frame,RooFit.Name( "ErfExp comp." ),RooFit.Components("model_bkg*"),RooFit.LineStyle(9),RooFit.LineColor(kBlue+2),RooFit.Normalization(1.0,RooAbsReal.RelativeExpected))
    pdfModel.plotOn(frame,RooFit.Name( "Double CB" ),RooFit.Components("model_ttbar_*"),RooFit.LineStyle(9),RooFit.LineColor(kRed+3),RooFit.Normalization(1.0,RooAbsReal.RelativeExpected))
    pdfModel.plotOn(frame,RooFit.Name( "Gaussian 1" ),RooFit.Components("gaus1*"),RooFit.LineStyle(kDashed),RooFit.LineColor(kRed+3),RooFit.Normalization(1.0,RooAbsReal.RelativeExpected))
    pdfModel.plotOn(frame,RooFit.Name( "Chebyshev comp." ),RooFit.Components("cheb*"),RooFit.LineStyle(kDashed),RooFit.LineColor(kBlue+3),RooFit.Normalization(1.0,RooAbsReal.RelativeExpected))
    pdfModel.plotOn(frame,RooFit.Name( "ErfExp Sig. comp." ),RooFit.Components("erfExp*"),RooFit.LineStyle(kDashed),RooFit.LineColor(kBlue+4),RooFit.Normalization(1.0,RooAbsReal.RelativeExpected))
    if(isData): dataset.plotOn(frame,RooFit.DataError(RooAbsData.Poisson),RooFit.Name(dataset.GetName ()))
    else: dataset.plotOn(frame,RooFit.DataError(RooAbsData.SumW2),RooFit.Name(dataset.GetName ()))
    c1.cd()
    frame.GetYaxis().SetNdivisions(203);
    frame.GetXaxis().SetNdivisions(202);
    frame.GetYaxis().SetTitleSize(0.05)
    frame.GetYaxis().SetTitleOffset(1.35)
    frame.SetName("mjjFit")
    frame.GetYaxis().SetTitle("A.U")
    frame.GetXaxis().SetTitle(title)
    frame.Draw()
    # frame.SetMinimum(0.)
    # frame.SetMaximum(2900.)
    legend = getLegend()
    if(isData): legend.AddEntry(frame.findObject(dataset.GetName ()),"CMS data","lpe")
    else: legend.AddEntry(frame.findObject(dataset.GetName ()),"Total MC","lpe")
    legend.AddEntry(frame.findObject(pdfModel.GetName()),"Sim. fit","l")
    if frame.findObject("Gaussian 1"):
      legend.AddEntry(frame.findObject("Gaussian 1"),frame.findObject("Gaussian 1").GetName(),"l")
    if frame.findObject("Chebyshev comp."):
      legend.AddEntry(frame.findObject("Chebyshev comp."),frame.findObject("Chebyshev comp.").GetName(),"l")
    if frame.findObject("Gaussian 2"):
      legend.AddEntry(frame.findObject("Gaussian 2"),frame.findObject("Gaussian 2").GetName(),"l")
    if frame.findObject("ErfExp comp."):
      legend.AddEntry(frame.findObject("ErfExp comp."),frame.findObject("ErfExp comp.").GetName(),"l")
    if frame.findObject("Double CB"):
      legend.AddEntry(frame.findObject("Double CB"),frame.findObject("Double CB").GetName(),"l")  
    legend.Draw("same")
    CMS_lumi(c1, iPeriod, iPos)
    addInfo = getPavetext()
    addInfo.AddText("#chi^{2}/nDOF = %.3f"%chi2)
    addInfo.Draw()
    c1.Update()
    dirname = "plots/"+options.workspace.replace('workspace_', '')
    c1.SaveAs(dirname+"/"+pdfModel.GetName()+".png")
    c1.SaveAs(dirname+"/"+pdfModel.GetName()+".pdf")
    c1.SaveAs(dirname+"/"+pdfModel.GetName()+".root")
    c1.SaveAs(dirname+"/"+pdfModel.GetName()+".C")
    return chi2
    


def doFitsToMatchedTT():
    
    f = TFile(options.workspace.replace(".root","")+".root")
    workspace4fit_ = f.Get("workspace4fit_")
    ttMC_fitter = initialiseFits("em", options.sample, options.minX, options.maxX, workspace4fit_)
        
        
    from WTopScalefactorProducer.Fitter.fitutils import fit_mj_single_MC
    
    fit_mj_single_MC(ttMC_fitter.workspace4fit_,ttMC_fitter.file_TTbar_mc,"_TTbar_realW",ttMC_fitter.mj_shape["TTbar_realW_MC"],ttMC_fitter.channel,ttMC_fitter.wtagger_label,options.workspace.replace(".root",""))
    fit_mj_single_MC(ttMC_fitter.workspace4fit_,ttMC_fitter.file_TTbar_mc,"_TTbar_realW_failtau2tau1cut",ttMC_fitter.mj_shape["TTbar_realW_fail_MC"],ttMC_fitter.channel,ttMC_fitter.wtagger_label,options.workspace.replace(".root",""))
    fit_mj_single_MC(ttMC_fitter.workspace4fit_,ttMC_fitter.file_TTbar_mc,"_TTbar_fakeW",ttMC_fitter.mj_shape["TTbar_fakeW_MC"],ttMC_fitter.channel,ttMC_fitter.wtagger_label,options.workspace.replace(".root",""))
    fit_mj_single_MC(ttMC_fitter.workspace4fit_,ttMC_fitter.file_TTbar_mc,"_TTbar_fakeW_failtau2tau1cut",ttMC_fitter.mj_shape["TTbar_fakeW_fail_MC"],ttMC_fitter.channel,ttMC_fitter.wtagger_label,options.workspace.replace(".root",""))

    print "Finished fitting matched tt MC! Plots can be found in plots/MCfits/_TT*"
        
def doFitsToMC():
    if options.doWS: 
        workspace4fit_ = RooWorkspace("workspace4fit_",options.workspace)
    else:
        f = TFile("workspace.root")
        workspace4fit_ = f.Get("workspace4fit_")
    boostedW_fitter_em = initialiseFits("em", options.sample, options.minX, options.maxX, workspace4fit_)
    boostedW_fitter_em.get_datasets_fit_minor_bkg()
    print "Finished fitting MC! Plots can be found in plots_*_MCfits. Printing workspace:"
#    workspace4fit_.Print()
                    
def GetWtagScalefactors(workspace,fitter):

    #------------- Calculate scalefactors -------------
    ### Efficiency in data and MC
    rrv_eff_MC_em   = workspace.var("eff_ttbar_TotalMC_em")
    rrv_mean_MC_em  = workspace.var("rrv_mean1_gaus_ttbar_TotalMC_em_mj")
    rrv_sigma_MC_em = workspace.var("rrv_sigma1_gaus_ttbar_TotalMC_em_mj")

    rrv_eff_data_em   = workspace.var("eff_ttbar_data_em")
    rrv_mean_data_em  = workspace.var("rrv_mean1_gaus_ttbar_data_em_mj")
    rrv_sigma_data_em = workspace.var("rrv_sigma1_gaus_ttbar_data_em_mj")

    ## GET HP SCALEFACTOR AND UNCERTIANTIES
    wtagger_sf_em             = rrv_eff_data_em.getVal()/rrv_eff_MC_em.getVal()
    wtagger_sf_em_err         = wtagger_sf_em * ( (rrv_eff_data_em.getError()/rrv_eff_data_em.getVal() )**2 + (rrv_eff_MC_em.getError()/rrv_eff_MC_em.getVal())**2 )**0.5

    wtagger_mean_shift_em     = rrv_mean_data_em.getVal()-rrv_mean_MC_em.getVal()
    wtagger_mean_shift_err_em = (rrv_mean_data_em.getError()**2 + rrv_mean_MC_em.getError()**2)**0.5

    wtagger_sigma_enlarge_em     = rrv_sigma_data_em.getVal()/rrv_sigma_MC_em.getVal()
    wtagger_sigma_enlarge_err_em = ((rrv_sigma_data_em.getError()/rrv_sigma_data_em.getVal())**2 + (rrv_sigma_MC_em.getError()/rrv_sigma_MC_em.getVal())**2 )**0.5* wtagger_sigma_enlarge_em

    mean_sf_error  = (rrv_mean_data_em.getVal()/rrv_mean_MC_em.getVal())   * ( (rrv_mean_data_em.getError()/rrv_mean_data_em.getVal())**2   +  (rrv_mean_MC_em.getError() /rrv_mean_MC_em.getVal())**2    )**0.5
    sigma_sf_error = (rrv_sigma_data_em.getVal()/rrv_sigma_MC_em.getVal()) * ( (rrv_sigma_data_em.getError()/rrv_sigma_data_em.getVal())**2 +  (rrv_sigma_MC_em.getError()/rrv_sigma_MC_em.getVal())**2   )**0.5
    eff_sf_error   = (rrv_eff_data_em.getVal()/rrv_eff_MC_em.getVal())     * ( (rrv_eff_data_em.getError()/rrv_eff_data_em.getVal())**2     +  (rrv_eff_MC_em.getError()  /rrv_eff_MC_em.getVal())**2     )**0.5

    ## GET EXTREME FAIL NUMBERS IN ORDER TO COMPUTE LP SF:
    rrv_number_ttbar_TotalMC_extremefailtau2tau1cut_em_mj = workspace.var("rrv_number_ttbar_TotalMC_extremefailtau2tau1cut_em_mj")
    rrv_number_ttbar_data_extremefailtau2tau1cut_em_mj    = workspace.var("rrv_number_ttbar_data_extremefailtau2tau1cut_em_mj")

    rrv_number_total_ttbar_TotalMC_em = workspace.var("rrv_number_ttbar_TotalMC_beforetau2tau1cut_em_mj")
    rrv_number_total_ttbar_data_em    = workspace.var("rrv_number_ttbar_data_beforetau2tau1cut_em_mj")

    # eff_MC_em_extremefail   = rrv_number_ttbar_TotalMC_extremefailtau2tau1cut_em_mj.getValV() / rrv_number_total_ttbar_TotalMC_em.getValV()
 #    eff_data_em_extremefail = rrv_number_ttbar_data_extremefailtau2tau1cut_em_mj.getValV()    / rrv_number_total_ttbar_data_em.getVaVl()
 #
 #    eff_MC_em_extremefail_error   = eff_MC_em_extremefail   * ( (rrv_number_ttbar_TotalMC_extremefailtau2tau1cut_em_mj.getError()/rrv_number_ttbar_TotalMC_extremefailtau2tau1cut_em_mj.getVal() )**2 + (rrv_number_total_ttbar_TotalMC_em.getError()/rrv_number_total_ttbar_TotalMC_em.getVal())**2 )**0.5
 #    eff_data_em_extremefail_error = eff_data_em_extremefail * ( (rrv_number_ttbar_data_extremefailtau2tau1cut_em_mj.getError()/rrv_number_ttbar_data_extremefailtau2tau1cut_em_mj.getVal()       )**2 + (rrv_number_total_ttbar_data_em.getError()   /rrv_number_total_ttbar_data_em.getVal()   )**2 )**0.5
 #
 #    eff_SF_extremefail       = eff_data_em_extremefail/eff_MC_em_extremefail
 #    eff_SF_extremefail_error = eff_SF_extremefail * ( (eff_data_em_extremefail_error/eff_data_em_extremefail)**2 + (eff_MC_em_extremefail_error/eff_MC_em_extremefail)**2 )**0.5
 #
 #
 #    # w/ extreme fail
 #    eff_MC_em_LP   = 1.-rrv_eff_MC_em.getVal()   - eff_MC_em_extremefail
 #    eff_data_em_LP = 1.-rrv_eff_data_em.getVal() - eff_data_em_extremefail
 #
 #    eff_MC_em_LP_err   = TMath.Sqrt( rrv_eff_MC_em.getError()  **2 + eff_MC_em_extremefail_error**2 )
 #    eff_data_em_LP_err = TMath.Sqrt( rrv_eff_data_em.getError()**2 + eff_data_em_extremefail_error**2 )
 #
 #    wtagger_sf_em_LP     = eff_data_em_LP / eff_MC_em_LP
 #    wtagger_sf_em_LP_err = wtagger_sf_em_LP * ( (eff_data_em_LP_err/eff_data_em_LP)**2 + (eff_MC_em_LP_err/eff_MC_em_LP)**2 )**0.5

    # w/o extreme fail
    tmpq_eff_MC_em_LP   = 1. - rrv_eff_MC_em.getVal()
    tmpq_eff_data_em_LP = 1. - rrv_eff_data_em.getVal()

    tmpq_eff_MC_em_LP_err   = TMath.Sqrt( rrv_eff_MC_em.getError()  **2)
    tmpq_eff_data_em_LP_err = TMath.Sqrt( rrv_eff_data_em.getError()**2)

    pureq_wtagger_sf_em_LP = tmpq_eff_data_em_LP / tmpq_eff_MC_em_LP
    pureq_wtagger_sf_em_LP_err = pureq_wtagger_sf_em_LP*TMath.Sqrt( (tmpq_eff_data_em_LP_err/tmpq_eff_data_em_LP)**2 + (tmpq_eff_MC_em_LP_err/tmpq_eff_MC_em_LP)**2 )


    #------------- Print results -------------
    print "--------------------------------------------------------------------------------------------"
    print "                                             HP                                             "
    print "--------------------------------------------------------------------------------------------"
    print "W-tagging SF      : %0.3f +/- %0.3f (rel. error = %0.1f percent)" %(wtagger_sf_em, wtagger_sf_em_err,(wtagger_sf_em_err/wtagger_sf_em*100))
    print "Mass shift [GeV]  : %0.3f +/- %0.3f" %(wtagger_mean_shift_em, wtagger_mean_shift_err_em)
    print "Mass resolution SF: %0.3f +/- %0.3f" %(wtagger_sigma_enlarge_em, wtagger_sigma_enlarge_err_em)
    print ""
    print "Parameter             Data               Simulation        Data/Simulation"
    print " < m >           %0.3f +/- %0.3f      %0.3f +/- %0.3f      %0.3f +/- %0.3f" %(rrv_mean_data_em.getVal(),rrv_mean_data_em.getError(),rrv_mean_MC_em.getVal(),rrv_mean_MC_em.getError()    , rrv_mean_data_em.getVal()/rrv_mean_MC_em.getVal()  ,  mean_sf_error)
    print " #sigma          %0.3f +/- %0.3f      %0.3f +/- %0.3f      %0.3f +/- %0.3f" %(rrv_sigma_data_em.getVal(),rrv_sigma_data_em.getError(),rrv_sigma_MC_em.getVal(),rrv_sigma_MC_em.getError(), rrv_sigma_data_em.getVal()/rrv_sigma_MC_em.getVal(),  sigma_sf_error)
    print ""
    print "HP W-tag eff+SF  %0.3f +/- %0.3f      %0.3f +/- %0.3f      %0.3f +/- %0.3f" %(rrv_eff_data_em.getVal(),rrv_eff_data_em.getError(),rrv_eff_MC_em.getVal(),rrv_eff_MC_em.getError()        , rrv_eff_data_em.getVal()/rrv_eff_MC_em.getVal()    ,  eff_sf_error)
    # print "--------------------------------------------------------------------------------------------"
   #  print "                                        EXTREME FAIL                                        "
   #  print "--------------------------------------------------------------------------------------------"
   #  print "Parameter                     Data            Simulation            Data/Simulation"
   #  print "Extreme fail eff+SF     %0.3f +/- %0.3f      %0.3f +/- %0.3f      %0.3f +/- %0.3f" %(eff_data_em_extremefail,eff_data_em_extremefail_error,eff_MC_em_extremefail,eff_MC_em_extremefail_error, eff_SF_extremefail, eff_SF_extremefail_error)
    print "--------------------------------------------------------------------------------------------"
    print "                                             LP                                             "
    print "--------------------------------------------------------------------------------------------"
    print "Parameter                               Data              Simulation         Data/Simulation"
    # print "LP W-tag eff+SF ( w/ext fail)      %0.3f +/- %0.3f      %0.3f +/- %0.3f      %0.3f +/- %0.3f" %(eff_data_em_LP,eff_data_em_LP_err,eff_MC_em_LP,eff_MC_em_LP_err,wtagger_sf_em_LP,wtagger_sf_em_LP_err)
    print "LP W-tag eff+SF (wo/ext fail)      %0.3f +/- %0.3f      %0.3f +/- %0.3f      %0.3f +/- %0.3f" %(tmpq_eff_data_em_LP,tmpq_eff_data_em_LP_err,tmpq_eff_MC_em_LP,tmpq_eff_MC_em_LP_err,pureq_wtagger_sf_em_LP,pureq_wtagger_sf_em_LP_err)
    print "--------------------------------------------------------------------------------------------"
    print "--------------------------------------------------------------------------------------------"
    print ""; print "";
    
    
    print ""; print "";
    print "TABLE"; print "";
    
    print " \\begin{table}[htbp]"
    print "    \centering"
    print "    \\begin{tabular}{|lccc|}"
    print "    \hline"
    print "    & m [GeV]           & $\sigma$~[GeV]     & W-tag efficiency\\\\"
    print "    $\\tau_{21} < %.2f$ & &&\\\\ \hline"   %(options.tau2tau1cutHP)
    print "    \hline"                                                                        
    print "    Data            & %.3f$\pm$ %.3f~GeV   & %.3f $\pm$ %.3f~GeV & %.3f $\pm$ %.3f\\\\"  %(rrv_mean_data_em.getVal(),rrv_mean_data_em.getError(),rrv_sigma_data_em.getVal(),rrv_sigma_data_em.getError(),rrv_eff_data_em.getVal(),rrv_eff_data_em.getError())
    print "    Simulation      & %.3f$\pm$ %.3f~GeV   & %.3f $\pm$ %.3f~GeV & %.3f $\pm$ %.3f\\\\"  %(rrv_mean_MC_em.getVal(),rrv_mean_MC_em.getError(),rrv_sigma_MC_em.getVal(),rrv_sigma_MC_em.getError(),rrv_eff_MC_em.getVal(),rrv_eff_MC_em.getError())
    print "    \hline"                                                                        
    print "    Data/simulation & %.3f$\pm$ %.3f       & %.3f $\pm$ %.3f     & %.3f $\pm$ %.3f\\\\"  %(rrv_mean_data_em.getVal()/rrv_mean_MC_em.getVal()  ,  mean_sf_error,rrv_sigma_data_em.getVal()/rrv_sigma_MC_em.getVal(),  sigma_sf_error,rrv_eff_data_em.getVal()/rrv_eff_MC_em.getVal()    ,  eff_sf_error)
    print "    \hline"
    print "    $%.2f < \\tau_{21} < %.2f$ & &&\\\\ \hline"   %(options.tau2tau1cutHP,options.tau2tau1cutLP)
    print "    \hline"                                                                        
    print "    Data            &    &  & %.3f $\pm$ %.3f\\\\"  %(tmpq_eff_data_em_LP,tmpq_eff_data_em_LP_err)
    print "    Simulation      &    &  & %.3f $\pm$ %.3f\\\\"  %(tmpq_eff_MC_em_LP,tmpq_eff_MC_em_LP_err)
    print "    \hline"                                                                        
    print "    Data/simulation &    &   & %.3f $\pm$ %.3f\\\\"  %(pureq_wtagger_sf_em_LP,pureq_wtagger_sf_em_LP_err)
    print "    \hline"
    print "    \end{tabular}"
    print " \end{table}"
    
    
    #Write results to file
    fitter.file_out_ttbar_control.write("\n                                     HP                                    ")
    fitter.file_out_ttbar_control.write("\n-----------------------------------------------------------------------------------------------------------------------------")
    fitter.file_out_ttbar_control.write("\n")
    fitter.file_out_ttbar_control.write("\nW-tagging SF      : %0.3f +/- %0.3f (rel. error = %.1f percent)" %(wtagger_sf_em, wtagger_sf_em_err, (wtagger_sf_em_err/wtagger_sf_em*100)))
    fitter.file_out_ttbar_control.write("\n")
    fitter.file_out_ttbar_control.write("\nMass shift [GeV]  : %0.3f +/- %0.3f" %(wtagger_mean_shift_em, wtagger_mean_shift_err_em))
    fitter.file_out_ttbar_control.write("\nMass resolution SF: %0.3f +/- %0.3f" %(wtagger_sigma_enlarge_em, wtagger_sigma_enlarge_err_em))
    fitter.file_out_ttbar_control.write("\n")
    fitter.file_out_ttbar_control.write("\nParameter                 Data                          Simulation                          Data/Simulation")
    fitter.file_out_ttbar_control.write("\n < m >              %0.3f +/- %0.3f                  %0.3f +/- %0.3f                        %0.3f +/- %0.3f" %(rrv_mean_data_em.getVal(),rrv_mean_data_em.getError(),rrv_mean_MC_em.getVal(),rrv_mean_MC_em.getError()    , rrv_mean_data_em.getVal()/rrv_mean_MC_em.getVal()  ,  mean_sf_error))
    fitter.file_out_ttbar_control.write("\n #sigma             %0.3f +/- %0.3f                  %0.3f +/- %0.3f                        %0.3f +/- %0.3f" %(rrv_sigma_data_em.getVal(),rrv_sigma_data_em.getError(),rrv_sigma_MC_em.getVal(),rrv_sigma_MC_em.getError(), rrv_sigma_data_em.getVal()/rrv_sigma_MC_em.getVal(),  sigma_sf_error))
    fitter.file_out_ttbar_control.write("\n")
    fitter.file_out_ttbar_control.write("\n")
    fitter.file_out_ttbar_control.write("\nHP W-tag eff+SF     %0.3f +/- %0.3f                  %0.3f +/- %0.3f                        %0.3f +/- %0.3f" %(rrv_eff_data_em.getVal(),rrv_eff_data_em.getError(),rrv_eff_MC_em.getVal(),rrv_eff_MC_em.getError(), rrv_eff_data_em.getVal()/rrv_eff_MC_em.getVal(),  eff_sf_error))
    fitter.file_out_ttbar_control.write("\n")
      # fitter.file_out_ttbar_control.write("\n-----------------------------------------------------------------------------------------------------------------------------")
    #   fitter.file_out_ttbar_control.write("\n                                EXTREME FAIL                               ")
    #   fitter.file_out_ttbar_control.write("\n-----------------------------------------------------------------------------------------------------------------------------")
    #   fitter.file_out_ttbar_control.write("\nParameter                     Data                          Simulation                          Data/Simulation")
    #   fitter.file_out_ttbar_control.write("\nExtreme fail eff+SF     %0.3f +/- %0.3f                  %0.3f +/- %0.3f                        %0.3f +/- %0.3f" %(eff_data_em_extremefail,eff_data_em_extremefail_error,eff_MC_em_extremefail,eff_MC_em_extremefail_error, eff_SF_extremefail, eff_SF_extremefail_error))
    #   fitter.file_out_ttbar_control.write("\n-----------------------------------------------------------------------------------------------------------------------------")
    fitter.file_out_ttbar_control.write("\n                                    LP                                     ")
    fitter.file_out_ttbar_control.write("\n-----------------------------------------------------------------------------------------------------------------------------")
    fitter.file_out_ttbar_control.write("\n")
    fitter.file_out_ttbar_control.write("\nParameter                                   Data                          Simulation                          Data/Simulation")
    # fitter.file_out_ttbar_control.write("\nLP W-tag eff+SF ( w/ext fail)         %0.3f +/- %0.3f                  %0.3f +/- %0.3f                        %0.3f +/- %0.3f" %(eff_data_em_LP,eff_data_em_LP_err,eff_MC_em_LP,eff_MC_em_LP_err,wtagger_sf_em_LP,wtagger_sf_em_LP_err))
    fitter.file_out_ttbar_control.write("\nLP W-tag eff+SF (wo/ext fail)         %0.3f +/- %0.3f                  %0.3f +/- %0.3f                        %0.3f +/- %0.3f" %(tmpq_eff_data_em_LP,tmpq_eff_data_em_LP_err,tmpq_eff_MC_em_LP,tmpq_eff_MC_em_LP_err,pureq_wtagger_sf_em_LP,pureq_wtagger_sf_em_LP_err))
    fitter.file_out_ttbar_control.write("\n")
    fitter.file_out_ttbar_control.write("\n-----------------------------------------------------------------------------------------------------------------------------")
    fitter.file_out_ttbar_control.write("\n \\begin{table}[htbp]"                                                   )
    fitter.file_out_ttbar_control.write("\n    \centering"                                                          )
    fitter.file_out_ttbar_control.write("\n    \\begin{tabular}{|lccc|}"                                            )
    fitter.file_out_ttbar_control.write("\n    \hline"                                                              )
    fitter.file_out_ttbar_control.write("\n    & m [GeV]           & $\sigma$~[GeV]     & W-tag efficiency\\\\"     )
    fitter.file_out_ttbar_control.write("\n    $\\tau_{21} < %.2f$ & &&\\\\ \hline"   %(options.tau2tau1cutHP)      )
    fitter.file_out_ttbar_control.write("\n    \hline"                                                                                                                                                                                                                                                                                           )
    fitter.file_out_ttbar_control.write("\n    Data            & %.3f$\pm$ %.3f~GeV   & %.3f $\pm$ %.3f~GeV & %.3f $\pm$ %.3f\\\\"  %(rrv_mean_data_em.getVal(),rrv_mean_data_em.getError(),rrv_sigma_data_em.getVal(),rrv_sigma_data_em.getError(),rrv_eff_data_em.getVal(),rrv_eff_data_em.getError())                                          )
    fitter.file_out_ttbar_control.write("\n    Simulation      & %.3f$\pm$ %.3f~GeV   & %.3f $\pm$ %.3f~GeV & %.3f $\pm$ %.3f\\\\"  %(rrv_mean_MC_em.getVal(),rrv_mean_MC_em.getError(),rrv_sigma_MC_em.getVal(),rrv_sigma_MC_em.getError(),rrv_eff_MC_em.getVal(),rrv_eff_MC_em.getError())                                                      )
    fitter.file_out_ttbar_control.write("\n    \hline"                                                                                                                                                                                                                                                                                            )
    fitter.file_out_ttbar_control.write("\n    Data/simulation & %.3f$\pm$ %.3f       & %.3f $\pm$ %.3f     & %.3f $\pm$ %.3f\\\\"  %(rrv_mean_data_em.getVal()/rrv_mean_MC_em.getVal()  ,  mean_sf_error,rrv_sigma_data_em.getVal()/rrv_sigma_MC_em.getVal(),  sigma_sf_error,rrv_eff_data_em.getVal()/rrv_eff_MC_em.getVal()    ,  eff_sf_error))
    fitter.file_out_ttbar_control.write("\n    \hline"                                                                                                                                                                                                                                                                                            )
    fitter.file_out_ttbar_control.write("\n    $%.2f < \\tau_{21} < %.2f$ & &&\\\\ \hline"   %(options.tau2tau1cutHP,options.tau2tau1cutLP)                                                                                                                                                                                                       )
    fitter.file_out_ttbar_control.write("\n    \hline"                                                                                                                                                                                                                                                                                            )
    fitter.file_out_ttbar_control.write("\n    Data            &    &  & %.3f $\pm$ %.3f\\\\"  %(tmpq_eff_data_em_LP,tmpq_eff_data_em_LP_err)                                                                                                                                                                                                     )
    fitter.file_out_ttbar_control.write("\n    Simulation      &    &  & %.3f $\pm$ %.3f\\\\"  %(tmpq_eff_MC_em_LP,tmpq_eff_MC_em_LP_err)                                                                                                                                                                                                         )
    fitter.file_out_ttbar_control.write("\n    \hline"                                                                                                                                                                                                                                                                                            )
    fitter.file_out_ttbar_control.write("\n    Data/simulation &    &   & %.3f $\pm$ %.3f\\\\"  %(pureq_wtagger_sf_em_LP,pureq_wtagger_sf_em_LP_err)                                                                                                                                                                                              )
    fitter.file_out_ttbar_control.write("\n    \hline"                                                                                                                                                                                                                                                                                            )
    fitter.file_out_ttbar_control.write("\n    \end{tabular}"                                                                                                                                                                                                                                                                                     )
    fitter.file_out_ttbar_control.write("\n \end{table}")
    
    
    if options.peak == "Wt":

        rrv_mean_MC_em  = workspace.var("rrv_mean1_gaus_bkg_TotalMC_failtau2tau1cut_em_mj") 
        rrv_sigma_MC_em = workspace.var("rrv_sigma1_gaus_bkg_TotalMC_failtau2tau1cut_em_mj")

        rrv_mean_data_em  = workspace.var("rrv_mean1_gaus_bkg_data_failtau2tau1cut_em_mj")
        rrv_sigma_data_em = workspace.var("rrv_sigma1_gaus_bkg_data_failtau2tau1cut_em_mj")
        
        wtagger_mean_shift_em     = rrv_mean_data_em.getVal()-rrv_mean_MC_em.getVal()
        wtagger_mean_shift_err_em = (rrv_mean_data_em.getError()**2 + rrv_mean_MC_em.getError()**2)**0.5

        wtagger_sigma_enlarge_em     = rrv_sigma_data_em.getVal()/rrv_sigma_MC_em.getVal()
        wtagger_sigma_enlarge_err_em = ((rrv_sigma_data_em.getError()/rrv_sigma_data_em.getVal())**2 + (rrv_sigma_MC_em.getError()/rrv_sigma_MC_em.getVal())**2 )**0.5* wtagger_sigma_enlarge_em

        mean_sf_error  = (rrv_mean_data_em.getVal()/rrv_mean_MC_em.getVal())   * ( (rrv_mean_data_em.getError()/rrv_mean_data_em.getVal())**2   +  (rrv_mean_MC_em.getError() /rrv_mean_MC_em.getVal())**2    )**0.5
        sigma_sf_error = (rrv_sigma_data_em.getVal()/rrv_sigma_MC_em.getVal()) * ( (rrv_sigma_data_em.getError()/rrv_sigma_data_em.getVal())**2 +  (rrv_sigma_MC_em.getError()/rrv_sigma_MC_em.getVal())**2   )**0.5
        print "FOR TOP:"
        print " \\begin{table}[htbp]"
        print "    \centering"
        print "    \\begin{tabular}{|lcc|}"
        print "    \hline"
        print "    & $m_{top}$ [GeV]           & $\sigma_{top}$~[GeV]\\\\"
        print "    $\\tau_{21} < %.2f$ & &\\\\ \hline"   %(options.tau2tau1cutHP)
        print "    \hline"                                                                        
        print "    Data            & %.3f$\pm$ %.3f~GeV   & %.3f $\pm$ %.3f~GeV \\\\"  %(rrv_mean_data_em.getVal(),rrv_mean_data_em.getError(),rrv_sigma_data_em.getVal(),rrv_sigma_data_em.getError())
        print "    Simulation      & %.3f$\pm$ %.3f~GeV   & %.3f $\pm$ %.3f~GeV \\\\"  %(rrv_mean_MC_em.getVal(),rrv_mean_MC_em.getError(),rrv_sigma_MC_em.getVal(),rrv_sigma_MC_em.getError())
        print "    \hline"                                                                                                                                             
        print "    Data/simulation & %.3f$\pm$ %.3f       & %.3f $\pm$ %.3f\\\\"  %(rrv_mean_data_em.getVal()/rrv_mean_MC_em.getVal()  ,  mean_sf_error,rrv_sigma_data_em.getVal()/rrv_sigma_MC_em.getVal(),  sigma_sf_error)
        print "    \hline"
        print "    \end{tabular}"
        print " \end{table}"
        
        fitter.file_out_ttbar_control.write("\n FOR TOP:")
        fitter.file_out_ttbar_control.write("\n \\begin{table}[htbp]"                                                                                                                                                                   )
        fitter.file_out_ttbar_control.write("\n    \centering"                                                                                                                                                                          )
        fitter.file_out_ttbar_control.write("\n    \\begin{tabular}{|lcc|}"                                                                                                                                                            )
        fitter.file_out_ttbar_control.write("\n    \hline"                                                                                                                                                                              )
        fitter.file_out_ttbar_control.write("\n    & $m_{top}$ [GeV]           & $\sigma_{top}$~[GeV]\\\\"                                                                                                                              )
        fitter.file_out_ttbar_control.write("\n    $\\tau_{21} < %.2f$ & &\\\\ \hline"   %(options.tau2tau1cutHP)                                                                                                                       )
        fitter.file_out_ttbar_control.write("\n    \hline"                                                                                                                                                                              )
        fitter.file_out_ttbar_control.write("\n    Data            & %.3f$\pm$ %.3f~GeV   & %.3f $\pm$ %.3f~GeV \\\\"  %(rrv_mean_data_em.getVal(),rrv_mean_data_em.getError(),rrv_sigma_data_em.getVal(),rrv_sigma_data_em.getError()) )
        fitter.file_out_ttbar_control.write("\n    Simulation      & %.3f$\pm$ %.3f~GeV   & %.3f $\pm$ %.3f~GeV \\\\"  %(rrv_mean_MC_em.getVal(),rrv_mean_MC_em.getError(),rrv_sigma_MC_em.getVal(),rrv_sigma_MC_em.getError())         )
        fitter.file_out_ttbar_control.write("\n    \hline"                                                                                                                                                                              )
        fitter.file_out_ttbar_control.write("    Data/simulation & %.3f$\pm$ %.3f       & %.3f $\pm$ %.3f\\\\"  %(rrv_mean_data_em.getVal()/rrv_mean_MC_em.getVal()  ,  mean_sf_error,rrv_sigma_data_em.getVal()/rrv_sigma_MC_em.getVal(),  sigma_sf_error))
        fitter.file_out_ttbar_control.write("    \hline")
        fitter.file_out_ttbar_control.write("\n    \end{tabular}")
        fitter.file_out_ttbar_control.write("\n \end{table}")
        
    
    
    
    
   
    
    
    
    
    csvf = open("%s.csv"%(options.workspace),'wb')
    writer = csv.writer(csvf)
    
    writer.writerow(["ptmin","ptmax","sf","err","effMC","errEffMC","effData","errEffData"])
    writer.writerows([[options.pTmin,options.pTmax, rrv_eff_data_em.getVal()/rrv_eff_MC_em.getVal(),  eff_sf_error, rrv_eff_MC_em.getVal(),rrv_eff_MC_em.getError(),rrv_eff_data_em.getVal(),rrv_eff_data_em.getError()]])
    csvf.close()
     


class initialiseFits:

    # Constructor: Input is channel (mu,ele,em), range in mj and a workspace
    def __init__(self, in_channel, in_sample, in_mj_min=50, in_mj_max=130, input_workspace=None):
      
      RooAbsPdf.defaultIntegratorConfig().setEpsRel(1e-9)
      RooAbsPdf.defaultIntegratorConfig().setEpsAbs(1e-9)
      
      # Set channel 
      self.channel = in_channel
      
      print "CHANNEL = %s" %in_channel
      print "Using Tau21 HP cut of " ,options.tau2tau1cutHP 

      # Map of shapes to be used for the fits (defined in ../python/PDFs/makepdf.py)                                                                                                                                         
      self.mj_shape = {}
      
      # Fit functions for matched tt MC
      #self.mj_shape["TTbar_realW_fail_MC"] = "GausErfExp_ttbar_failtau2tau1cut_fitMC"
      #self.mj_shape["TTbar_realW_MC"]      = "GausErfExp_ttbar_fitMC" #before "2Gaus_ttbar"
      
      self.mj_shape["TTbar_realW_fail_MC"]  = "DoubleSidedCB_ttbar_failtau2tau1cut_fitMC"                       
      self.mj_shape["TTbar_realW_MC"]       = "DoubleSidedCB_ttbar_fitMC"                                       
      self.mj_shape["TTbar_fakeW_fail_MC"]  = "ErfExp_ttbar_failtau2tau1cut_fitMC"                         
      self.mj_shape["TTbar_fakeW_MC"]       = "ErfExp_ttbar_fitMC"                                         
                                                                                                           
      # Use the same fit functions in data                                                                 
      self.mj_shape["bkg_data_fail"]        = self.mj_shape["TTbar_fakeW_fail_MC"].replace("_fitMC","")    
      self.mj_shape["signal_data_fail"]     = self.mj_shape["TTbar_realW_fail_MC"].replace("_fitMC","")    
      self.mj_shape["signal_data"]          = self.mj_shape["TTbar_realW_MC"].replace("_fitMC","")         
      self.mj_shape["bkg_data"]             = self.mj_shape["TTbar_fakeW_MC"].replace("_fitMC","")         
                                                                                                           
      # ... and in MC                                                                                      
      self.mj_shape["bkg_mc_fail"]          = self.mj_shape["TTbar_fakeW_fail_MC"].replace("_fitMC","")    
      self.mj_shape["signal_mc_fail"]       = self.mj_shape["TTbar_realW_fail_MC"].replace("_fitMC","")    
      self.mj_shape["signal_mc"]            = self.mj_shape["TTbar_realW_MC"].replace("_fitMC","")         
      self.mj_shape["bkg_mc"]               = self.mj_shape["TTbar_fakeW_MC"].replace("_fitMC","")         
 
      # Fit functions for minor backgrounds
      self.mj_shape["VV"]                   = "ExpGaus"
      self.mj_shape["VV_fail"]              = "ExpGaus"
      self.mj_shape["WJets"]                = "ErfExp"
      self.mj_shape["WJets_fail"]           = "ErfExp"
      self.mj_shape["QCD"]                  = "ErfExp"
      self.mj_shape["QCD_fail"]             = "ErfExp"
      self.mj_shape["STop"]                 = "ErfExpGaus_sp"       
      self.mj_shape["STop_fail"]            = "ErfExpGaus_sp"  
       
      #Need to add a second gauss when fitting top 
      if options.peak == "Wt" :
         self.mj_shape["STop_fail"]              = "Gaus2ErfExp"  
         self.mj_shape["TTbar_fakeW_fail_MC"]    = "ErfExpGauss_ttbar_failtau2tau1cut_fitMC"
         self.mj_shape["bkg_mc_fail"]            = "ErfExpGauss_ttbar_failtau2tau1cut"
         self.mj_shape["bkg_data_fail"]          = "ErfExpGauss_ttbar_failtau2tau1cut"
         # self.mj_shape["TTbar_fakeW_MC"]         = "ErfExpGauss_ttbar_fitMC"
         # self.mj_shape["bkg_mc"]                 = "ErfExpGauss_ttbar"
         # self.mj_shape["bkg_data"]               = "ErfExpGauss_ttbar"
      
      #Set lumi  
      self.Lumi=1.

          
      self.BinWidth_mj = 5.
      self.narrow_factor = 1.

      self.BinWidth_mj = self.BinWidth_mj/self.narrow_factor
      nbins_mj         = int( (in_mj_max - in_mj_min) / self.BinWidth_mj )
      in_mj_max        = in_mj_min+nbins_mj*self.BinWidth_mj
      
      jetMass = "PUPPI softdrop jet mass"

      rrv_mass_j = RooRealVar("rrv_mass_j", jetMass ,(in_mj_min+in_mj_max)/2.,in_mj_min,in_mj_max,"GeV")
      rrv_mass_j.setBins(nbins_mj)
 
      # Create workspace and import fit variable
      self.workspace4fit_ = input_workspace
      getattr(self.workspace4fit_,"import")(rrv_mass_j)

      # Signal region between 65 and 105 GeV
      self.mj_sideband_lo_min = in_mj_min
      self.mj_sideband_lo_max = 65
      self.mj_signal_min      = 65
      self.mj_signal_max      = 105
      self.mj_sideband_hi_min = 105
      self.mj_sideband_hi_max = in_mj_max
 
      # Setting ranges...
      rrv_mass_j.setRange("sb_lo",self.mj_sideband_lo_min,self.mj_sideband_lo_max) # 50-65 GeV
      rrv_mass_j.setRange("signal_region",self.mj_signal_min,self.mj_signal_max)   # 65-105 GeV
      rrv_mass_j.setRange("sb_hi",self.mj_sideband_hi_min,self.mj_sideband_hi_max) # 105-130 GeV
      rrv_mass_j.setRange("controlsample_fitting_range",in_mj_min,in_mj_max) 
        
      
      
      
      self.file_Directory       = "/eos/home-m/mhuwiler/data/Wtagging/Mergedefinition2017/"
      self.list_file_data       = ["SingleMuon-Run2018A.root", "SingleMuon-Run2018B.root", "SingleMuon-Run2018C.root", "SingleMuon-Run2018D.root"]
      self.list_file_TTbar_mc   = ["TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8.root", "TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8.root"]
      if options.topShower: self.list_file_TTbar_mc   = ["TT_TuneCH3_13TeV-powheg-herwig7.root"]
      if options.topGen: self.list_file_TTbar_mc   = ["TTJets_TuneCP5_13TeV-amcatnloFXFX-pythia8.root"]
      self.list_file_WJets_mc   = ["WJetsToLNu_HT-70To100_TuneCP5_13TeV-madgraphMLM-pythia8.root", "WJetsToLNu_HT-100To200_TuneCP5_13TeV-madgraphMLM-pythia8.root", "WJetsToLNu_HT-200To400_TuneCP5_13TeV-madgraphMLM-pythia8.root", "WJetsToLNu_HT-400To600_TuneCP5_13TeV-madgraphMLM-pythia8.root", "WJetsToLNu_HT-600To800_TuneCP5_13TeV-madgraphMLM-pythia8.root", "WJetsToLNu_HT-800To1200_TuneCP5_13TeV-madgraphMLM-pythia8.root", "WJetsToLNu_HT-1200To2500_TuneCP5_13TeV-madgraphMLM-pythia8.root", "WJetsToLNu_HT-2500ToInf_TuneCP5_13TeV-madgraphMLM-pythia8.root"]
      self.list_file_STop_mc    = ["ST_s-channel_4f_leptonDecays_TuneCP5_13TeV-madgraph-pythia8.root", "ST_t-channel_antitop_4f_InclusiveDecays_TuneCP5_13TeV-powheg-madspin-pythia8.root", "ST_t-channel_top_4f_InclusiveDecays_TuneCP5_13TeV-powheg-madspin-pythia8.root", "ST_tW_antitop_5f_inclusiveDecays_TuneCP5_13TeV-powheg-pythia8.root", "ST_tW_top_5f_inclusiveDecays_TuneCP5_13TeV-powheg-pythia8.root"] #["ST_t-channel_antitop_5f_TuneCP5_13TeV-powheg-pythia8.root", "ST_t-channel_top_5f_TuneCP5_13TeV-powheg-pythia8.root", "ST_tW_antitop_5f_NoFullyHadronicDecays_TuneCP5_13TeV-powheg-pythia8.root", "ST_tW_top_5f_NoFullyHadronicDecays_TuneCP5_13TeV-powheg-pythia8.root"]
      self.list_file_VV_mc      = ["WW_TuneCP5_13TeV-pythia8.root", "WZ_TuneCP5_13TeV-pythia8.root", "ZZ_TuneCP5_13TeV-pythia8.root"]
      #self.list_file_QCD_mc     = 
#      self.list_file_WJets_mc  += ["QCD_HT500to700_TuneCP5_13TeV-madgraphMLM-pythia8.root", "QCD_HT700to1000_TuneCP5_13TeV-madgraphMLM-pythia8.root", "QCD_HT1000to1500_TuneCP5_13TeV-madgraphMLM-pythia8.root", "QCD_HT1500to2000_TuneCP5_13TeV-madgraphMLM-pythia8.root", "QCD_HT2000toInf_TuneCP5_13TeV-madgraphMLM-pythia8.root"] #"QCD_HT100to200_TuneCP5_13TeV-madgraphMLM-pythia8.root", "QCD_HT200to300_TuneCP5_13TeV-madgraphMLM-pythia8.root", "QCD_HT300to500_TuneCP5_13TeV-madgraphMLM-pythia8.root", 
      # self.list_file_TTbar_mc   = ["thaarres_TTJets_SingleLeptFromT_TuneCP5_13TeV-madgraphMLM-pythia8.root"]
#      if options.sample.find("amcnlo")!=-1: 
#          self.list_file_TTbar_mc   = ["thaarres_TTJets_TuneCP5_13TeV-amcatnloFXFX-pythia8.root"]
#      if options.sample.find("tune16")!=-1: 
#          self.list_file_TTbar_mc   = ["thaarres_TTToSemiLeptonic_WspTgt150_TuneCUETP8M2T4_13TeV-powheg-pythia8.root"]
  
      
      
      
      # Directory and input files
      # self.file_Directory         = "/mnt/t3nfs01/data01/shome/thaarres/2017/Treemaker/TreeAnalyzer/Output/HaddedOutput/reweighted/"
      postfix = ""
          
      self.file_data              = "SingleMuon.root"
      self.file_WJets_mc          = "WJetsToLNu.root"
      self.file_VV_mc             = "VV.root"   
      self.file_QCD_mc            = "QCD.root" 
      self.file_STop_mc           = "ST.root"
      self.file_TTbar_mc          = "TT.root"
      self.file_pseudodata        = "pseudodata_weighted.root"
      
      #self.list_file_QCD_mc     = ["QCD_HT1000to1500_TuneCP5_13TeV-madgraph-pythia8.root","QCD_HT100to200_TuneCP5_13TeV-madgraph-pythia8.root","QCD_HT1500to2000_TuneCP5_13TeV-madgraph-pythia8.root","QCD_HT200to300_TuneCP5_13TeV-madgraph-pythia8.root","QCD_HT300to500_TuneCP5_13TeV-madgraph-pythia8.root","QCD_HT700to1000_TuneCP5_13TeV-madgraph-pythia8.root"]
      #self.list_file_STop_mc    = ["ST_s-channel_4f_leptonDecays_TuneCP5_PSweights_13TeV-amcatnlo-pythia8.root","ST_t-channel_antitop_4f_inclusiveDecays_TuneCP5_13TeV-powhegV2-madspin-pythia8.root","ST_t-channel_top_4f_inclusiveDecays_TuneCP5_13TeV-powhegV2-madspin-pythia8.root","ST_tW_antitop_5f_inclusiveDecays_TuneCP5_13TeV-powheg-pythia8.root","ST_tW_top_5f_inclusiveDecays_TuneCP5_PSweights_13TeV-powheg-pythia8.root"]
      #self.list_file_data       = ["SingleMuon_Run2017B-17Nov2017-v1.root","SingleMuon_Run2017C-17Nov2017-v1.root","SingleMuon_Run2017D-17Nov2017-v1.root","SingleMuon_Run2017E-17Nov2017-v1.root","SingleMuon_Run2017F-17Nov2017-v1.root"]
      #self.list_file_TTbar_mc   = ["TTTo2L2Nu_TuneCP5_PSweights_13TeV-powheg-pythia8.root","TTToHadronic_TuneCP5_PSweights_13TeV-powheg-pythia8.root","TTToSemiLeptonic_TuneCP5_PSweights_13TeV-powheg-pythia8.root"]
      #if options.sample.find("tune16")!=-1:
      #    self.list_file_TTbar_mc   = ["TTTo2L2Nu_TuneCP5_PSweights_13TeV-powheg-pythia8.root","TTToHadronic_TuneCP5_PSweights_13TeV-powheg-pythia8.root","TTToSemiLeptonic_WspTgt150_TuneCUETP8M2T4_13TeV-powheg-pythia8.root"]
      #    
      #    
      ## self.list_file_TTbar_mc   = ["TTTo2L2Nu_TuneCP5_PSweights_13TeV-powheg-pythia8.root","TTToHadronic_TuneCP5_PSweights_13TeV-powheg-pythia8.root","TTToSemiLeptonic_WspTgt150_TuneCUETP8M2T4_13TeV-powheg-pythia8.root"]
      #self.list_file_WJets_mc   = ["W1JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8.root","W2JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8.root","W3JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8.root","W4JetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8.root"]
      #self.list_file_VV_mc      = ["WW_TuneCP5_13TeV-pythia8.root","WZ_TuneCP5_13TeV-pythia8.root","ZZ_TuneCP5_13TeV-pythia8.root"]
      self.list_file_pseudodata =  self.list_file_STop_mc + self.list_file_VV_mc   + self.list_file_WJets_mc + self.list_file_TTbar_mc
      # self.list_file_data              = ["SingleMuon.root"]
#       self.list_file_WJets_mc           = ["WJetsToLNu.root"]
#       self.list_file_VV_mc             = ["VV.root"]
#       self.list_file_QCD_mc            = ["QCD.root"]
#       self.list_file_STop_mc           = ["ST.root"]
#       self.list_file_TTbar_mc          = ["TT.root"]
#       self.list_file_pseudodata        = ["tmp_TT.root","WJetsToLNu.root","VV.root","QCD.root","ST.root"]#"pseudodata_weighted.root"    #Important! ROOT tree containing all backgrounds added together (tt+singleT+VV+Wjets). Used for fit to total MC
      

      # Define Tau21 WP
      self.wtagger_label = "HP"
      self.wtagger_cut = options.tau2tau1cutHP
      self.wtagger_cut_min = 0.
          
      
      # Define label used for plots and choosing fit paramters in PDFs/MakePdf.cxx  
      wp = "%.2f" %options.tau2tau1cutHP
      wp = wp.replace(".","v")
      self.wtagger_label = self.wtagger_label + "%s%s%s"%(wp,in_sample,postfix) 

      
      #Color pallett for plots
      fillcolor = [434,613,633,414]
      self.color_palet = {}
      self.color_palet["data"]              = 1
      self.color_palet["WJets"]             = 633
      self.color_palet["VV"]                = 613
      self.color_palet["QCD"]               = 797
      self.color_palet["STop"]              = 434
      self.color_palet["TTbar"]             = 414
      self.color_palet["TTbar_realW"]       = 414
      self.color_palet["TTbar_fakeW"]       = 415
      self.color_palet["Signal"]            = 1
      self.color_palet["Uncertainty"]       = 1
      self.color_palet["Other_Backgrounds"] = 1    
      
      self.AK8_pt_min   = options.pTmin
      self.AK8_pt_max   = options.pTmax  
   
      # Out .txt file with final SF numbers
      self.file_ttbar_control_txt = "%s.txt"%(options.workspace)
      self.file_out_ttbar_control = open(self.file_ttbar_control_txt.replace("__","_"),"w")
                                                                                                                                                            
    def get_datasets_fit_minor_bkg(self):
        
        filename = options.workspace.replace(".root","")+".root"
        print "Checking if workspace exists, if not, produce " ,filename
        try: os.stat(filename)
        except: options.doWS = True
        if options.doWS:
            
            print "No workspace found! Looping over infiles and creating datasets, output in " , filename
         
            rrv_mass_j = self.workspace4fit_.var("rrv_mass_j")
            self.get_mj_dataset(self.list_file_STop_mc,"_STop")
            self.get_mj_dataset(self.list_file_WJets_mc,"_WJets")
            self.get_mj_dataset(self.list_file_VV_mc,"_VV")
            # self.get_mj_dataset(self.list_file_QCD_mc,"_QCD")
            if options.fitMC: return
            self.get_mj_dataset(self.list_file_TTbar_mc,"_TTbar")
            self.get_mj_dataset(self.list_file_TTbar_mc,"_TTbar_realW")
            self.get_mj_dataset(self.list_file_TTbar_mc,"_TTbar_fakeW")
            self.get_mj_dataset(self.list_file_data,"_data")
            from WTopScalefactorProducer.Fitter.fitutils import doTTscalefactor
            ttSF = doTTscalefactor(self.workspace4fit_,self.channel)
#            for f in self.list_file_TTbar_mc:
#              fname  = rt.TString(self.file_Directory+"/"+f)
#              print "scaling with tt SF: " ,fname
#              fileIn = TFile(fname.Data())
#              treeIn = fileIn.Get("tree")
#              treeIn.SetWeight(ttSF)
#              treeIn.AutoSave()
#              fileIn.Close()
            self.get_mj_dataset(self.list_file_pseudodata,"_TotalMC")
            print "Saving workspace in %s! To save time when debugging use option --WS %s to avoid recreating workspace every time"%(options.workspace+".root",options.workspace+".root")
            
            self.workspace4fit_.writeToFile(filename)
            
            from WTopScalefactorProducer.Fitter.fitutils import fit_mj_single_MC
            
            #First fit to gen level variables
            fit_mj_single_MC(self.workspace4fit_,self.file_TTbar_mc,"_TTbar_realW",self.mj_shape["TTbar_realW_MC"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))
            fit_mj_single_MC(self.workspace4fit_,self.file_TTbar_mc,"_TTbar_realW_failtau2tau1cut",self.mj_shape["TTbar_realW_fail_MC"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))
            fit_mj_single_MC(self.workspace4fit_,self.file_TTbar_mc,"_TTbar_fakeW",self.mj_shape["TTbar_fakeW_MC"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))
            fit_mj_single_MC(self.workspace4fit_,self.file_TTbar_mc,"_TTbar_fakeW_failtau2tau1cut",self.mj_shape["TTbar_fakeW_fail_MC"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))
            
            fit_mj_single_MC(self.workspace4fit_,self.file_STop_mc,"_STop"                        ,self.mj_shape["STop"],self.channel,self.wtagger_label,options.workspace.replace(".root","")) 
            fit_mj_single_MC(self.workspace4fit_,self.file_STop_mc,"_STop_failtau2tau1cut"        ,self.mj_shape["STop_fail"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))      
            fit_mj_single_MC(self.workspace4fit_,self.file_WJets_mc,"_WJets",self.mj_shape["WJets"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))
            fit_mj_single_MC(self.workspace4fit_,self.file_WJets_mc,"_WJets_failtau2tau1cut",self.mj_shape["WJets_fail"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))       
            fit_mj_single_MC(self.workspace4fit_,self.file_VV_mc,"_VV",self.mj_shape["VV"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))
            fit_mj_single_MC(self.workspace4fit_,self.file_VV_mc,"_VV_failtau2tau1cut",self.mj_shape["VV_fail"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))
            # fit_mj_single_MC(self.workspace4fit_,self.file_QCD_mc,"_QCD",self.mj_shape["QCD"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))
            # fit_mj_single_MC(self.workspace4fit_,self.file_QCD_mc,"_QCD_failtau2tau1cut",self.mj_shape["QCD_fail"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))
        
        else:
            
            from WTopScalefactorProducer.Fitter.fitutils import fit_mj_single_MC
            fit_mj_single_MC(self.workspace4fit_,self.file_STop_mc,"_STop"                        ,self.mj_shape["STop"],self.channel,self.wtagger_label,options.workspace.replace(".root","")) 
            fit_mj_single_MC(self.workspace4fit_,self.file_STop_mc,"_STop_failtau2tau1cut"        ,self.mj_shape["STop_fail"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))          
            fit_mj_single_MC(self.workspace4fit_,self.file_WJets_mc,"_WJets",self.mj_shape["WJets"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))
            fit_mj_single_MC(self.workspace4fit_,self.file_WJets_mc,"_WJets_failtau2tau1cut",self.mj_shape["WJets_fail"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))           
            fit_mj_single_MC(self.workspace4fit_,self.file_VV_mc,"_VV",self.mj_shape["VV"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))
            fit_mj_single_MC(self.workspace4fit_,self.file_VV_mc,"_VV_failtau2tau1cut",self.mj_shape["VV_fail"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))
            # fit_mj_single_MC(self.workspace4fit_,self.file_QCD_mc,"_QCD",self.mj_shape["QCD"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))
            # fit_mj_single_MC(self.workspace4fit_,self.file_QCD_mc,"_QCD_failtau2tau1cut",self.mj_shape["QCD_fail"],self.channel,self.wtagger_label,options.workspace.replace(".root",""))
            
    def get_sim_fit_components(self):
      # self.print_yields()
      self.constrainslist_data = []
      self.constrainslist_mc   = []
        
      #Construct pass/fail models (fix minor backgrounds, create sim. fit total PDFS)
      from WTopScalefactorProducer.Fitter.fitutils import ScaleFactorTTbarControlSampleFit
      ScaleFactorTTbarControlSampleFit(self.workspace4fit_,self.mj_shape,self.color_palet,self.constrainslist_data,self.constrainslist_mc,self.channel,self.wtagger_label,options.peak,options.workspace.replace(".root",""))
     
      #Get data/MC scalefactors
      rrv_scale_number                      = self.workspace4fit_.var("rrv_scale_number_TTbar_STop_VV_WJets").getVal()
      rrv_scale_number_fail                 = self.workspace4fit_.var("rrv_scale_number_TTbar_STop_VV_WJets_fail").getVal()
      
      #Print data/MC scalefactors
      print " Pass MC / all data = %.3f" %(rrv_scale_number)
      print " Fail MC / all data = %.3f" %(rrv_scale_number_fail)
        
    def print_yields(self):

        # Print dataset yields in the signal region
#        print ""
#        print ""
#        print ""
#        self.workspace4fit_.var("rrv_number_dataset_signal_region_data_"    +self.channel+"_mj").Print()
#        self.workspace4fit_.var("rrv_number_dataset_signal_region_VV_"      +self.channel+"_mj").Print()
#        self.workspace4fit_.var("rrv_number_dataset_signal_region_WJets_"  +self.channel+"_mj").Print()
#        self.workspace4fit_.var("rrv_number_dataset_signal_region_QCD_"     +self.channel+"_mj").Print()
#        self.workspace4fit_.var("rrv_number_dataset_signal_region_STop_"    +self.channel+"_mj").Print()
#        self.workspace4fit_.var("rrv_number_dataset_signal_region_TTbar_"   +self.channel+"_mj").Print()
#        print ""
#        print ""
#        print ""

        number_dataset_signal_region_data_mj                      = self.workspace4fit_.var("rrv_number_dataset_signal_region_data_"+self.channel+"_mj").getVal()
        number_dataset_signal_region_error2_data_mj               = self.workspace4fit_.var("rrv_number_dataset_signal_region_error2_data_"+self.channel+"_mj").getVal()
        
        number_dataset_signal_region_TotalMC_mj                   = self.workspace4fit_.var("rrv_number_dataset_signal_region_TotalMC_"+self.channel+"_mj").getVal()
        number_dataset_signal_region_error2_TotalMC_mj            = self.workspace4fit_.var("rrv_number_dataset_signal_region_error2_TotalMC_"+self.channel+"_mj").getVal()
        
        number_dataset_signal_region_before_cut_data_mj           = self.workspace4fit_.var("rrv_number_dataset_signal_region_before_cut_data_"+self.channel+"_mj").getVal()
        number_dataset_signal_region_before_cut_error2_data_mj    = self.workspace4fit_.var("rrv_number_dataset_signal_region_before_cut_error2_data_"+self.channel+"_mj").getVal()
        
        number_dataset_signal_region_before_cut_TotalMC_mj        = self.workspace4fit_.var("rrv_number_dataset_signal_region_before_cut_TotalMC_"+self.channel+"_mj").getVal()
        number_dataset_signal_region_before_cut_error2_TotalMC_mj = self.workspace4fit_.var("rrv_number_dataset_signal_region_before_cut_error2_TotalMC_"+self.channel+"_mj").getVal()
        
        wtagger_eff_MC                                            = number_dataset_signal_region_TotalMC_mj/number_dataset_signal_region_before_cut_TotalMC_mj
        wtagger_eff_data                                          = number_dataset_signal_region_data_mj/number_dataset_signal_region_before_cut_data_mj

        wtagger_eff_reweight                                      = wtagger_eff_data/wtagger_eff_MC
        wtagger_eff_reweight_err                                  = wtagger_eff_reweight*TMath.Sqrt(number_dataset_signal_region_error2_data_mj/number_dataset_signal_region_data_mj/number_dataset_signal_region_data_mj + number_dataset_signal_region_error2_TotalMC_mj/number_dataset_signal_region_TotalMC_mj/number_dataset_signal_region_TotalMC_mj +number_dataset_signal_region_before_cut_error2_data_mj/number_dataset_signal_region_before_cut_data_mj/number_dataset_signal_region_data_mj + number_dataset_signal_region_before_cut_error2_TotalMC_mj/number_dataset_signal_region_before_cut_TotalMC_mj/number_dataset_signal_region_before_cut_TotalMC_mj)
        
        print ""
        print "Nr. data events in signal_region                  : %s +/- sqrt(%s)"%(number_dataset_signal_region_data_mj, number_dataset_signal_region_error2_data_mj**.5)
        print ""
        print "Nr. MC events in signal_region                    : %s +/- sqrt(%s)"%(number_dataset_signal_region_TotalMC_mj, number_dataset_signal_region_error2_TotalMC_mj)
        print ""
        print "Nr. dataevents in signalregion before cut on tau21: %s +/- sqrt(%s)"%(number_dataset_signal_region_before_cut_data_mj, number_dataset_signal_region_before_cut_error2_data_mj)
        print ""
        print "Nr. MC events in signalregion before cut on tau21 : %s +/- sqrt(%s) "%(number_dataset_signal_region_before_cut_TotalMC_mj, number_dataset_signal_region_before_cut_error2_TotalMC_mj)
        print ""                                                     
        print "W-tagging efficiency (pre-fit):"
        print "W-tagging eff. MC       = %.3f "%(wtagger_eff_MC)
        print "W-tagging eff. data     = %.3f "%(wtagger_eff_data)
        print "W-tagging SF            = %.3f +/- %.3f"%(wtagger_eff_reweight, wtagger_eff_reweight_err)
        print ""
        print ""
        
        self.file_out_ttbar_control.write("%s channel SF: \n"%(self.channel))
        self.file_out_ttbar_control.write("Nr. events in signal_region                        : %s +/- sqrt(%s)\n"%(number_dataset_signal_region_data_mj, number_dataset_signal_region_error2_data_mj))
        self.file_out_ttbar_control.write("Nr. TotalMC in signal_region                       : %s +/- sqrt(%s) \n"%(number_dataset_signal_region_TotalMC_mj, number_dataset_signal_region_error2_TotalMC_mj))
        self.file_out_ttbar_control.write("event number of data in signalregion before_cut    : %s +/- sqrt(%s)\n"%(number_dataset_signal_region_before_cut_data_mj, number_dataset_signal_region_before_cut_error2_data_mj))
        self.file_out_ttbar_control.write("event number of TotalMC in signal_region before_cut: %s +/- sqrt(%s) \n"%(number_dataset_signal_region_before_cut_TotalMC_mj, number_dataset_signal_region_before_cut_error2_TotalMC_mj))
        self.file_out_ttbar_control.write("wtagger_eff_MC         = %s       \n"%(wtagger_eff_MC ))
        self.file_out_ttbar_control.write("wtagger_eff_data       = %s       \n"%(wtagger_eff_data ))
        self.file_out_ttbar_control.write("wtagger_eff_reweight   = %s +/- %s\n"%(wtagger_eff_reweight, wtagger_eff_reweight_err))
 
    # Loop over trees
    def get_mj_dataset(self,in_file_name, label, jet_mass=options.massvar,lumi=lumi): 
      
      print "Using mass variable " ,jet_mass
    
      treeIn = TChain(options.intree)
      for f in in_file_name:
        print "Using file: ", TString(self.file_Directory+f)
        fileIn_name = TString(self.file_Directory+f)  
        treeIn.Add(fileIn_name.Data())
      
       #Get in tree
      # treeIn      = fileIn.Get(options.intree)
      
      rrv_mass_j = self.workspace4fit_.var("rrv_mass_j")
      rrv_weight = RooRealVar("rrv_weight","rrv_weight",0. ,10000000.)

      # Mj dataset before tau2tau1 cut : Passed
      rdataset_mj     = RooDataSet("rdataset"     +label+"_"+self.channel+"_mj","rdataset"    +label+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) )
      rdataset4fit_mj = RooDataSet("rdataset4fit" +label+"_"+self.channel+"_mj","rdataset4fit"+label+"_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) )
      # rrv_number_pass = RooRealVar("rrv_number_ttbar"+label+"_passtau2tau1cut_em_mj","rrv_number_ttbar"+label+"_passtau2tau1cut_em_mj",0.,10000000.) #LUCA
  
      # Mj dataset before tau2tau1 cut : Total
      rdataset_beforetau2tau1cut_mj     = RooDataSet("rdataset"     +label+"_beforetau2tau1cut_"+self.channel+"_mj","rdataset"    +label+"_beforetau2tau1cut_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) )
      rdataset4fit_beforetau2tau1cut_mj = RooDataSet("rdataset4fit" +label+"_beforetau2tau1cut_"+self.channel+"_mj","rdataset4fit"+label+"_beforetau2tau1cut_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) )
      # rrv_number_before = RooRealVar("rrv_number_ttbar"+label+"_beforetau2tau1cut_em_mj","rrv_number_ttbar"+label+"_beforetau2tau1cut_em_mj",0.,10000000.) #LUCA
 
      ### Mj dataset failed tau2tau1 cut :
      rdataset_failtau2tau1cut_mj     = RooDataSet("rdataset"     +label+"_failtau2tau1cut_"+self.channel+"_mj","rdataset"    +label+"_failtau2tau1cut_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) )
      rdataset4fit_failtau2tau1cut_mj = RooDataSet("rdataset4fit" +label+"_failtau2tau1cut_"+self.channel+"_mj","rdataset4fit"+label+"_failtau2tau1cut_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) )
      # rrv_number_fail = RooRealVar("rrv_number_ttbar"+label+"_failingtau2tau1cut_em_mj","rrv_number_ttbar"+label+"_failingtau2tau1cut_em_mj",0.,10000000.) #LUCA

      ### Mj dataset extreme failed tau2tau1 cut: > 0.75
      rdataset_extremefailtau2tau1cut_mj     = RooDataSet("rdataset"    +label+"_extremefailtau2tau1cut_"+self.channel+"_mj","rdataset"     +label+"_extremefailtau2tau1cut_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) )
      rdataset4fit_extremefailtau2tau1cut_mj = RooDataSet("rdataset4fit"+label+"_extremefailtau2tau1cut_"+self.channel+"_mj","rdataset4fit" +label+"_extremefailtau2tau1cut_"+self.channel+"_mj",RooArgSet(rrv_mass_j,rrv_weight),RooFit.WeightVar(rrv_weight) )
      rrv_number_extremefail = RooRealVar("rrv_number_ttbar"+label+"_extremefailtau2tau1cut_em_mj","rrv_number_ttbar"+label+"_extremefailtau2tau1cut_em_mj",0.,10000000.) #LUCA
      
      
      # Define categories
      if self.workspace4fit_.cat("category_p_f"+"_"+self.channel):
        category_p_f = self.workspace4fit_.cat("category_p_f"+"_"+self.channel)
      else:
        category_p_f = RooCategory("category_p_f"+"_"+self.channel,"category_p_f"+"_"+self.channel)
        category_p_f.defineType("pass")
        category_p_f.defineType("fail")
        getattr(self.workspace4fit_,"import")(category_p_f)
      
      combData_p_f = RooDataSet("combData_p_f"+label+"_"+self.channel,"combData_p_f"+label+"_"+self.channel,RooArgSet(rrv_mass_j, category_p_f, rrv_weight),RooFit.WeightVar(rrv_weight))
      
      print "N entries: ", treeIn.GetEntries()
      
      hnum_4region                    = TH1D("hnum_4region"       +label+"_"+self.channel,"hnum_4region"        +label+"_"+self.channel,4, -1.5, 2.5) # m_j -1: sb_lo; 0:signal_region; 1: sb_hi; 2:total
      hnum_4region_error2             = TH1D("hnum_4region_error2"+label+"_"+self.channel,"hnum_4region_error2" +label+"_"+self.channel,4, -1.5, 2.5) # m_j -1: sb_lo; 0:signal_region; 1: sb_hi; 2:total

      hnum_4region_before_cut         = TH1D("hnum_4region_before_cut"        +label+"_"+self.channel,"hnum_4region_before_cut"       +label+"_"+self.channel,4,-1.5,2.5);# m_j -1: sb_lo; 0:signal_region; 1: sb_hi; 2:total
      hnum_4region_before_cut_error2  = TH1D("hnum_4region_before_cut_error2" +label+"_"+self.channel,"hnum_4region_before_cut_error2"+label+"_"+self.channel,4,-1.5,2.5);# m_j -1: sb_lo; 0:signal_region; 1: sb_hi; 2:total

      hnum_2region                    = TH1D("hnum_2region"       +label+"_"+self.channel,"hnum_2region"        +label+"_"+self.channel,2,-0.5,1.5);# m_lvj 0: signal_region; 1: total --> There is only 1 and that is SIGNAL REGION?!
      hnum_2region_error2             = TH1D("hnum_2region_error2"+label+"_"+self.channel,"hnum_2region_error2" +label+"_"+self.channel,2,-0.5,1.5);# m_lvj 0: signal_region; 1: total
      
  
      #-------------------------------------------------------------------------------------------
      
      # Loop over tree entries
      print "rrv_mass_j.getMax() = " ,rrv_mass_j.getMax()
      print "rrv_mass_j.getMin() = " ,rrv_mass_j.getMin()
      tmp_scale_to_lumi = 1
      i = 0
      
      SF = 1.0
#      if label.find("QCD")!=-1: 
#          SF = 0.697187387981
      
      for i in range(treeIn.GetEntries()):
          if i % 5000 == 0: print "iEntry: ",i
          event = treeIn.GetEntry(i)
          if not (treeIn.SelectedJet_pt > self.AK8_pt_min): continue
          if not (treeIn.SelectedJet_pt < self.AK8_pt_max): continue
          if not (treeIn.passedMETfilters):continue
          if not (treeIn.maxAK4CSV>0.8484):continue

          if getattr(treeIn, jet_mass) > rrv_mass_j.getMax() and getattr(treeIn, jet_mass)< rrv_mass_j.getMin() : continue
          
#          try:
#            if TString(label).Contains("realW") and not getattr(treeIn,"genmatchedAK8"): #mergedVTruth Is a real W, meaning both daughters of W is withing jet cone!!
#              continue
#            if TString(label).Contains("realW") and getattr(treeIn,"genmatchedAK8"): #mergedTopTruth Is a real top, meaning both daughters of W and b is withing jet cone!!
#              continue
#              
#            if TString(label).Contains("fakeW") and getattr(treeIn,"genmatchedAK8") and not getattr(treeIn,"genmatchedAK8"): #mergedVTruth mergedTopTruth
#                continue
#          except:
#            print "WARNING: no genmatchedAK8 in tree", treeIn.GetName()
          
          if TString(label).Contains("realW") and not treeIn.genmatchedAK82017: continue
          if TString(label).Contains("fakeW") and treeIn.genmatchedAK82017: continue
          
          if options.tagger.find("ddt")==-1 and options.tagger.find("DDT")==-1: 
              wtagger = getattr(treeIn,options.tagger)
          else: 
              wtagger = treeIn.SelectedJet_tau21_ddt_retune #treeIn.jetAK8_tau21+(0.079*rt.TMath.Log((treeIn.jetAK8_softDrop_mass*treeIn.jetAK8_softDrop_mass)/treeIn.jetAK8_pt))
            
          discriminantCut = 0
          if wtagger <= options.tau2tau1cutHP: # HP
              discriminantCut = 2
          elif wtagger > options.tau2tau1cutHP and wtagger <= options.tau2tau1cutLP: #LP
              discriminantCut = 1
          elif wtagger > options.tau2tau1cutLP: # Extreme fail
              discriminantCut = 0

          tmp_jet_mass = getattr(treeIn, jet_mass);
          treeWeight = treeIn.GetWeight()
          
          # if i==0:
            
          
          if not TString(label).Contains("data"):

              tmp_scale_to_lumi = treeIn.eventweightlumi ## weigth for xs and lumi FIXME
              if options.topPt: tmp_scale_to_lumi *= treeIn.topweight
#              # tmp_event_weight  = treeWeight*treeIn.normGenWeight*treeIn.puWeight*treeIn.eventWeightLumi*treeIn.topWeight*lumi*SF#*treeIn.muTrigWeight*treeIn.muIsoWeight
#              if options.topPt:
#                tmp_event_weight  = treeWeight*treeIn.normGenWeight*treeIn.puWeight*treeIn.topWeight*treeIn.eventWeightLumi*lumi*SF
#              else:             
#                tmp_event_weight  = treeWeight*treeIn.normGenWeight*treeIn.puWeight*treeIn.eventWeightLumi*lumi*SF # no topPt
#              
#              # tmp_event_weight4fit = treeWeight*treeIn.normGenWeight*treeIn.puWeight*treeIn.topWeight*SF#*treeIn.muTrigWeight*treeIn.muIsoWeight
#              if options.topPt: 
#                tmp_event_weight4fit = treeWeight*treeIn.normGenWeight*treeIn.puWeight*treeIn.topWeight*SF
#              else:
#                tmp_event_weight4fit = treeWeight*treeIn.normGenWeight*treeIn.puWeight*SF # no topPt
              
#              tmp_event_weight4fit = tmp_event_weight4fit*treeIn.eventWeightLumi/tmp_scale_to_lumi    
              tmp_event_weight = tmp_scale_to_lumi
              tmp_event_weight4fit = tmp_scale_to_lumi
              
          else:
            tmp_scale_to_lumi = 1.
            tmp_event_weight = 1.
            tmp_event_weight4fit = 1.

          
          # if options.fitTT:
          #   tmp_event_weight4fit = 1.
                   

          #  HP category
          if discriminantCut == 2  and tmp_jet_mass > rrv_mass_j.getMin() and tmp_jet_mass < rrv_mass_j.getMax():   
             rrv_mass_j.setVal(tmp_jet_mass)
             
             rdataset_mj    .add(RooArgSet(rrv_mass_j), tmp_event_weight)
             rdataset4fit_mj.add(RooArgSet(rrv_mass_j), tmp_event_weight4fit)

             if tmp_jet_mass >= self.mj_sideband_lo_min and tmp_jet_mass < self.mj_sideband_lo_max:
                 hnum_4region.Fill(-1,tmp_event_weight )
                 
             if tmp_jet_mass >= self.mj_signal_min and tmp_jet_mass < self.mj_signal_max:
                 # hnum_2region.Fill(1,tmp_event_weight)
                 hnum_4region.Fill(0,tmp_event_weight)
                 hnum_4region_error2.Fill(0,tmp_event_weight*tmp_event_weight)
             if tmp_jet_mass >= self.mj_sideband_hi_min and tmp_jet_mass < self.mj_sideband_hi_max:
                 hnum_4region.Fill(1,tmp_event_weight)

             hnum_4region.Fill(2,tmp_event_weight) 
             
             category_p_f.setLabel("pass")
             combData_p_f.add(RooArgSet(rrv_mass_j,category_p_f),tmp_event_weight)
          
          # TOTAL category (no Tau21 )
          if (discriminantCut == 2 or discriminantCut == 1 or discriminantCut == 0) and (rrv_mass_j.getMin() < tmp_jet_mass < rrv_mass_j.getMax()): 
              rrv_mass_j.setVal(tmp_jet_mass)

              if tmp_jet_mass >= self.mj_signal_min and tmp_jet_mass <self.mj_signal_max :
                 hnum_4region_before_cut.Fill(0,tmp_event_weight)
                 hnum_4region_before_cut_error2.Fill(0,tmp_event_weight*tmp_event_weight)

              rdataset_beforetau2tau1cut_mj.add(RooArgSet(rrv_mass_j),tmp_event_weight)
              rdataset4fit_beforetau2tau1cut_mj.add(RooArgSet(rrv_mass_j),tmp_event_weight4fit)
          
          # 1 minus HP category (LP)   
          if (discriminantCut==1) and (rrv_mass_j.getMin() < tmp_jet_mass < rrv_mass_j.getMax()):
  
              rrv_mass_j.setVal(tmp_jet_mass)

              rdataset_failtau2tau1cut_mj     .add(RooArgSet(rrv_mass_j), tmp_event_weight)
              rdataset4fit_failtau2tau1cut_mj .add(RooArgSet(rrv_mass_j), tmp_event_weight4fit )
    
              category_p_f.setLabel("fail");
              combData_p_f.add(RooArgSet(rrv_mass_j,category_p_f),tmp_event_weight)
           #-------------------------------------------------------------------------------------------
           # Extreme fail category (Tau21 > LP_max)   
          if discriminantCut==0 and (rrv_mass_j.getMin() < tmp_jet_mass < rrv_mass_j.getMax()):

            rdataset_extremefailtau2tau1cut_mj     .add(RooArgSet(rrv_mass_j), tmp_event_weight)
            rdataset4fit_extremefailtau2tau1cut_mj .add(RooArgSet(rrv_mass_j), tmp_event_weight4fit )
      
      rrv_scale_to_lumi                        = RooRealVar("rrv_scale_to_lumi"+label+"_"                       +self.channel,"rrv_scale_to_lumi"+label+"_"                       +self.channel,tmp_scale_to_lumi*SF)
      rrv_scale_to_lumi_failtau2tau1cut        = RooRealVar("rrv_scale_to_lumi"+label+"_failtau2tau1cut_"       +self.channel,"rrv_scale_to_lumi"+label+"_failtau2tau1cut_"       +self.channel,tmp_scale_to_lumi*SF)
      rrv_scale_to_lumi_extremefailtau2tau1cut = RooRealVar("rrv_scale_to_lumi"+label+"_extremefailtau2tau1cut_"+self.channel,"rrv_scale_to_lumi"+label+"_extremefailtau2tau1cut_"+self.channel,tmp_scale_to_lumi*SF)
      
      getattr(self.workspace4fit_,"import")(rrv_scale_to_lumi)
      getattr(self.workspace4fit_,"import")(rrv_scale_to_lumi_failtau2tau1cut)
      getattr(self.workspace4fit_,"import")(rrv_scale_to_lumi_extremefailtau2tau1cut)
        
      # rrv_number_pass.setVal(rdataset_mj.sumEntries())
 #      rrv_number_pass.setError(TMath.Sqrt(rdataset_mj.sumEntries()))
 #      # rrv_number_pass.Print()
 #      rrv_number_before.setVal(rdataset_beforetau2tau1cut_mj.sumEntries())
 #      rrv_number_before.setError(TMath.Sqrt(rdataset_beforetau2tau1cut_mj.sumEntries()))
 #      # rrv_number_before.Print()
 #      rrv_number_fail.setVal(rdataset_failtau2tau1cut_mj.sumEntries())
 #      rrv_number_fail.setError(TMath.Sqrt(rdataset_failtau2tau1cut_mj.sumEntries()))
 #      # rrv_number_fail.Print()
      rrv_number_extremefail.setVal(rdataset_extremefailtau2tau1cut_mj.sumEntries())
      rrv_number_extremefail.setError(TMath.Sqrt(rdataset_extremefailtau2tau1cut_mj.sumEntries()))
      getattr(self.workspace4fit_,"import")(rrv_number_extremefail)

#      rrv_number_extremefail.Print()
 #
      # getattr(self.workspace4fit_,"import")(rrv_number_pass)
    #   getattr(self.workspace4fit_,"import")(rrv_number_before)
    #   getattr(self.workspace4fit_,"import")(rrv_number_fail)
      

      #prepare m_j dataset
      rrv_number_dataset_sb_lo_mj                 = RooRealVar("rrv_number_dataset_sb_lo"               +label+"_"+self.channel+"_mj","rrv_number_dataset_sb_lo"                +label+"_"+self.channel+"_mj",hnum_4region.GetBinContent(1))
      rrv_number_dataset_signal_region_mj         = RooRealVar("rrv_number_dataset_signal_region"       +label+"_"+self.channel+"_mj","rrv_number_dataset_signal_region"        +label+"_"+self.channel+"_mj",hnum_4region.GetBinContent(2))
      rrv_number_dataset_signal_region_error2_mj  = RooRealVar("rrv_number_dataset_signal_region_error2"+label+"_"+self.channel+"_mj","rrv_number_dataset_signal_region_error2" +label+"_"+self.channel+"_mj",hnum_4region_error2.GetBinContent(2))

      rrv_number_dataset_signal_region_before_cut_mj        = RooRealVar("rrv_number_dataset_signal_region_before_cut"        +label+"_"+self.channel+"_mj","rrv_number_dataset_signal_region_before_cut"       +label+"_"+self.channel+"_mj",hnum_4region_before_cut.GetBinContent(2))
      rrv_number_dataset_signal_region_before_cut_error2_mj = RooRealVar("rrv_number_dataset_signal_region_before_cut_error2" +label+"_"+self.channel+"_mj","rrv_number_dataset_signal_region_before_cut_error2"+label+"_"+self.channel+"_mj",hnum_4region_before_cut_error2.GetBinContent(2))
      rrv_number_dataset_sb_hi_mj                           = RooRealVar("rrv_number_dataset_sb_hi"                           +label+"_"+self.channel+"_mj","rrv_number_dataset_sb_hi"                          +label+"_"+self.channel+"_mj",hnum_4region.GetBinContent(3))

      getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_lo_mj)
      getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_mj)
      getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_error2_mj)
      getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_before_cut_mj)
      getattr(self.workspace4fit_,"import")(rrv_number_dataset_signal_region_before_cut_error2_mj)
      getattr(self.workspace4fit_,"import")(rrv_number_dataset_sb_hi_mj)
      getattr(self.workspace4fit_,"import")(combData_p_f)

      print "N_rdataset_mj: "
      getattr(self.workspace4fit_,"import")(rdataset_mj)
      getattr(self.workspace4fit_,"import")(rdataset4fit_mj)
      getattr(self.workspace4fit_,"import")(rdataset_beforetau2tau1cut_mj)
      getattr(self.workspace4fit_,"import")(rdataset4fit_beforetau2tau1cut_mj)
      getattr(self.workspace4fit_,"import")(rdataset_failtau2tau1cut_mj)
      getattr(self.workspace4fit_,"import")(rdataset4fit_failtau2tau1cut_mj)
      getattr(self.workspace4fit_,"import")(rdataset_extremefailtau2tau1cut_mj)
      getattr(self.workspace4fit_,"import")(rdataset4fit_extremefailtau2tau1cut_mj)
      

#from __future__ import print_function
def tracefunc(frame, event, arg, indent=[0], displayOnReturn=False):
      excluded = ["__call__", "__init__", "__getattr2", "_importhook", "cleanup", "_remove", "_run_exitfuncs"] # vetoing frequent python functions from being output 
      funcname = frame.f_code.co_name
      arguments = frame.f_code.co_varnames  #co_argcount
#      for i in arguments: 
#        sys.stderr.write(i)
#        sys.stderr.write(" ")
#      sys.stderr.write(" \n")
      if event == "call":
          indent[0] += 2
          if funcname not in excluded: 
             sys.stderr.write("-" * indent[0] + "> call function {}()\n".format(funcname)) #print("-" * indent[0] + "> call function", funcname, file=sys.stderr)
             sys.stderr.write(" " * indent[0])
             #sys.stderr.write(arguments)
      elif event == "return":
          if funcname not in excluded and displayOnReturn: 
             sys.stderr.write("<" + "-" * indent[0] + "exit function {}()\n".format(funcname))
          indent[0] -= 2
      return tracefunc

sys.setprofile(tracefunc)

### Start  main
if __name__ == '__main__':
    channel = options.channel ## ele, mu or ele+mu combined

    fitter = WTaggingFitter(options)

    fitter.FitMC()

    #fitter.TestFitControl()

    fitter.FitControlRegion()

    #fitter.TestFit()


#    if options.fitTT:
#        print "Doing fits to matched tt MC. Tree must contain branch with flag for match/no-match to generator level W!"
#        cmd = 'rm ttfit_parameters%s.txt'%options.workspace.replace(".root","")
#        os.system(cmd)
#        cmd = 'rm fitres*%s*.txt'%options.workspace.replace(".root","")
#        os.system(cmd)
#        doFitsToMatchedTT()
#    elif options.fitMC:
#        print "Doing fits to MC only"
#        doFitsToMC()
#    else:
#        print 'Getting W-tagging scalefactor for %s sample for n-subjettiness < %.2f' %(channel,options.tau2tau1cutHP) #I am actually not doing a simoultaneous fit. So..... change this
#        getSF()


