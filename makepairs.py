__author__ = 'Julie'

from nltk.corpus import wordnet as wn
import random,json


def notmultiword(lemma):
    words=lemma.split('_')
    if len(words)==1:
        return True
    else:
        return False

def generate_mono_list(lemmalist):
    print "Number of WN lemmas = "+str(len(lemmalist))
    monolist=[]
    mwcount=0
    singlesense=0
    lowfreq=0
    predcount=0
    nonpred=0
    for lemma in lemmalist[0:]:
        if notmultiword(lemma):
            #print lemma, wn.synsets(lemma,pos=wn.NOUN)
            if len(wn.synsets(lemma,pos=wn.NOUN))==1:
                freq=0
                for form in wn.lemmas(lemma,wn.NOUN):
                    freq+=form.count()
                if freq>0:
                    singlesense+=1
                    monolist.append(lemma)
                else:
                    lowfreq+=1
            else:
                total=0
                max=0
                for form in wn.lemmas(lemma,wn.NOUN):
                    thiscount=form.count()
                    #print form,thiscount
                    total+=thiscount
                    if thiscount>max:
                        max=thiscount
                if max > (total)/2:
                    predcount+=1
                    monolist.append(lemma)
                    #print "Accepting "+lemma
                else:
                    nonpred+=1

        else:
            #print "lemma "+lemma+" not added as multiword"
            mwcount+=1

    print "Accepted single sense words "+str(singlesense)
    print "Accepted predominant sense words "+str(predcount)
    print "TOTAL accepted "+str(singlesense+predcount)
    print "Rejected single sense words with no freq info "+str(lowfreq)
    print "Rejected non predominant sense words "+str(nonpred)
    print "Rejected multiwords "+str(mwcount)
    return monolist

def find_hypernyms(sensedict,filterA,filterB,ratio,include_ancestors):

    hyperrels=[]
    hyporels=[]
    totaldist=0
    for asynset in sensedict.keys():

        ancestors = asynset.hypernym_distances()
        hyps=[]
        for (ancestor,distance) in ancestors:
            if include_ancestors and distance > 0:
                hyps.append((ancestor,distance))
            elif distance == 1:
                hyps.append((ancestor,distance))

        #hyps = asynset.hypernyms()
        added=0
        for (hyp,dist) in hyps:
            
            if hyp in sensedict.keys():
                if (len(hyperrels)+len(hyporels))%ratio > 0 and asynset not in filterA:

                    if hyp not in filterB:
                        hyperrels.append((sensedict[asynset],sensedict[hyp]))
                        filterA.append(asynset)
                        filterB.append(hyp)
                        totaldist+=dist
                        added+=1

                elif asynset not in filterB:
                    if hyp not in filterA:
                        hyporels.append((sensedict[hyp],sensedict[asynset]))
                        filterA.append(hyp)
                        filterB.append(asynset)
                        totaldist+=dist
                        added+=1
            if added>1: break

    print len(hyperrels),hyperrels
    print len(hyporels),hyporels
    average = (totaldist*1.0)/(len(hyperrels)+len(hyporels))
    print "Average distance = "+str(average)
    return (hyperrels,hyporels,filterA,filterB)

def find_simpairs(sensedict):
    sims=[]
    for asynset in sensedict.keys():
        for bsynset in sensedict.keys():
            if asynset != bsynset:
                sim =asynset.path_similarity(bsynset)
                if sim > 0.2: sims.append((sensedict[asynset],sensedict[bsynset]))

    print len(sims)
    print sims
    return sims

def find_coords(sensedict,filterA,filterB,max):
    rels=[]
    for asynset in sensedict.keys():
        if len(rels)> max:
            break
        if asynset not in filterA:
            hypers = asynset.hypernyms()
            for hyper in hypers:
                hypos = hyper.hyponyms()
                for hypo in hypos:
                    if hypo != asynset and hypo not in filterB:
                        if hypo in sensedict.keys():
                            pair = (sensedict[asynset],sensedict[hypo])
                            rev = (sensedict[hypo],sensedict[asynset])
                            if pair not in rels and rev not in rels:
                                rels.append(pair)
                                filterA.append(asynset)
                                filterB.append(hypo)
                                break
    print len(rels)
    print rels
    return (rels,filterA,filterB)

if __name__=="__main__":

    include_ancestors=True

#    royalty=wn.synsets('royalty',wn.NOUN)
#    bribe = wn.synsets('bribe',wn.NOUN)
#    for s in royalty:
#        print s, s.definition, s.hypernyms(),s.hypernym_distances()
#    royaltylemmas=wn.lemmas('royalty',wn.NOUN)
#    for s in royaltylemmas:
#        print s, s.count()
#    for s in bribe:
#        print s, s.definition, s.hypernyms(), s.hypernym_distances()
#
#    exit()

    wordlist=generate_mono_list([x for x in wn.all_lemma_names(pos=wn.NOUN)])
    print wordlist
    sensedict={wn.synsets(alemma,wn.NOUN)[0] : alemma for alemma in wordlist}
    (hyperpairs,hypopairs,filterA,filterB)=find_hypernyms(sensedict,[],[],3,include_ancestors)
    #simpairs=find_simpairs(sensedict)
    (coordpairs,filterA,filterB) = find_coords(sensedict,filterA,filterB,len(hyperpairs)+len(hypopairs))

    #write entailment pairs
    poslength=len(hyperpairs)
    neglength = poslength/2
    outlist = []
    for (w1,w2) in hyperpairs:
        outlist.append([w1,w2,1])
    random.seed(42)
    random.shuffle(hypopairs)
    random.shuffle(coordpairs)
    for (w1,w2) in hypopairs[0:neglength]:
        outlist.append([w1,w2,0])
    for (w1,w2) in coordpairs[0:poslength-neglength]:
        outlist.append([w1,w2,0])

    with open('entpairs2.json','w') as outpath:
        json.dump(outlist,outpath)

    #write coordinate pairs
    poslength = len(hyperpairs)+len(hypopairs)
    outlist=[]
    for (w1,w2) in hyperpairs:
        outlist.append([w1,w2,0])
    for (w1,w2) in hypopairs:
        outlist.append([w1,w2,0])
    for (w1,w2) in coordpairs[0:poslength]:
        outlist.append([w1,w2,1])
    with open('coordpairs2.json','w') as outpath:
        json.dump(outlist,outpath)

