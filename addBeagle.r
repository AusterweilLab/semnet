library(R.matlab)
library(data.table)

allsubs<-c("S101","S102","S103","S104","S105","S106","S107","S108","S109","S110","S111","S112","S113","S114","S115","S116","S117","S118","S119","S120")

# human data
#humans<-fread('animals_1500.csv')
setkey(humans,subj)

# MATLAB files
rawmat<-readMat('BEAGLEdata.mat')
beagle<-rawmat[5]$BEAGLE.sim
lbls<-rawmat[4]$BEAGLE.labels
lbls<-unlist(lbls)
cats<-rawmat$BEAGLE.animalClassesIdxMatrix

checkBeagle <- function(word1,word2) {
    word1<-toupper(word1)
    word2<-toupper(word2)
    idx1<-match(word1,lbls)
    idx2<-match(word2,lbls)
    beagle[idx1,idx2]
}

# extract BEAGLE values and add to data table
loadBEAGLEvals <- function() {
    beaglevals<-c()
    for (i in seq(nrow(humans))) {
        link1<-toupper(humans[i,link1])
        link2<-toupper(humans[i,link2])
        idx1<-match(link1,lbls)
        idx2<-match(link2,lbls)

        if (is.na(idx1) | is.na(idx2)) {
            beaglevals<-c(beaglevals,NA)
        } else {
            beaglevals<-c(beaglevals,beagle[idx1,idx2])
        }
    }
    # append beagle values to human data
    humans[,beagle:=beaglevals]
}

# use BEAGLE x Troyer category matrix (771x22) to see if links share a category
sameCats <- function() {
    catvals<-c()
    for (i in seq(nrow(humans))) {
        link1<-toupper(humans[i,link1])
        link2<-toupper(humans[i,link2])
        idx1<-match(link1,lbls)
        idx2<-match(link2,lbls)
        sharecat<-any(cats[idx1,]>0 & cats[idx2,]>0)
        catvals<-c(catvals,sharecat)
    }
    humans[,sharecat:=catvals]
}

# Find avg BEAGLE value of all possible link combos (per participant)
beagleRand <- function() {
    for (sb in unique(humans[,subj])) {
        nodes<-unique(c(humans[sb,][,link1],humans[sb,][,link2]))
        nodeidx<-unlist(lapply(nodes, function(node) { match(toupper(node),lbls) }))
        nodeidx<-nodeidx[!is.na(nodeidx)]
        combos<-combn(nodeidx,2)
        beaglevals<-c()
        for (i in seq(ncol(combos))) {
            beaglevals<-c(beaglevals,beagle[combos[1,i],combos[2,i]])
        }
        humans[sb,beaglerand:=mean(beaglevals)]
    }
}

# probability of two random nodes in graph sharing a category
catRand <- function() {
    for (sb in unique(humans[,subj])) {
        nodes<-unique(c(humans[sb,][,link1],humans[sb,][,link2]))
        nodeidx<-unlist(lapply(nodes, function(node) { match(toupper(node),lbls) }))
        nodeidx<-nodeidx[!is.na(nodeidx)]
        combos<-combn(nodeidx,2)
        catvals<-c()
        for (i in seq(ncol(combos))) {
            sharecat<-any(cats[combos[1,i]]>0 & cats[combos[2,i]]>0)
            catvals<-c(catvals,sharecat)
        }
        humans[sb,catrand:=mean(catvals)]
    }
}

loadBEAGLEvals()
beagleRand()
humans[,beaglediff:=beagle-beaglerand]

sameCats()
catRand()

# BEAGLE test: INVITE vs IRT5
t.test(humans[invite==0 & irt5==1,mean(beaglediff,na.rm=T),by=subj][,V1])  # adds quality links!
t.test(humans[invite==1 & irt5==0,mean(beaglediff,na.rm=T),by=subj][,V1])  # removes quality links :(
t.test(humans[invite==1 & irt5==0,mean(beaglediff,na.rm=T),by=subj][,V1],humans[invite==0 & irt5==1,mean(beaglediff,na.rm=T),by=subj][,V1]) # added links are better than removed links, but not significantly

# Troyer test: INVITE vs IRT5
# IRT9 > INVITE > RW > IRT5
# only significant test is EVERYTHING > IRT5
t.test(humans[invite==1,mean(sharecat,na.rm=T),keyby=subj][,V1],humans[irt5==1,mean(sharecat,na.rm=T),keyby=subj][,V1],paired=T)



