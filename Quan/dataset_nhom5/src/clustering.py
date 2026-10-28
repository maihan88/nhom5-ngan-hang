import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from utils import *

def run(d):
    # Phân tích mô tả toàn kỳ, không dùng nhãn hoặc đầu vào dự báo CAR Q4.
    scaler=StandardScaler(); x=scaler.fit_transform(d[FIN])
    scores=[]; candidates={}
    for k in range(2,7):
        m=KMeans(n_clusters=k,random_state=42,n_init='auto').fit(x)
        candidates[k]=m
        scores.append({'K':k,'Inertia':m.inertia_,'Silhouette':silhouette_score(x,m.labels_),'smallest_cluster':int(np.bincount(m.labels_).min())})
    table=pd.DataFrame(scores)
    chosen=int(table.loc[table.Silhouette.idxmax(),'K'])
    final=candidates[chosen]
    labeled=d[KEY+FIN].copy(); labeled['cluster']=final.labels_
    profile=labeled.groupby('cluster')[FIN].mean()
    profile['observations']=labeled.groupby('cluster').size()
    standardized=(profile[FIN]-d[FIN].mean())/d[FIN].std(ddof=0)
    names={}
    for c,row in standardized.iterrows():
        top=row.abs().nlargest(2).index
        names[c]=' / '.join(f'{feature.upper()} '+('cao tương đối' if row[feature]>0 else 'thấp tương đối') for feature in top)
    profile['description']=profile.index.map(names)
    labeled['description']=labeled.cluster.map(names)
    pca=PCA(n_components=2,random_state=42); pcs=pca.fit_transform(x)
    labeled['PC1'],labeled['PC2']=pcs[:,0],pcs[:,1]
    variance=pd.DataFrame({'PC':['PC1','PC2'],'explained_variance_ratio':pca.explained_variance_ratio_,'cumulative':np.cumsum(pca.explained_variance_ratio_)})
    loadings=pd.DataFrame(pca.components_.T,index=FIN,columns=['PC1','PC2']).rename_axis('Feature').reset_index()
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    axes[0].plot(table.K,table.Inertia,'o-'); axes[0].set(xlabel='K',ylabel='Inertia',title='Elbow')
    axes[1].plot(table.K,table.Silhouette,'o-'); axes[1].set(xlabel='K',ylabel='Silhouette',title='Silhouette')
    fig.tight_layout(); fig.savefig(FIGURES/'k_selection.png',dpi=160); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,6))
    for c in sorted(labeled.cluster.unique()):
        sub=labeled[labeled.cluster==c]; ax.scatter(sub.PC1,sub.PC2,label=f'{c}: n={len(sub)}',alpha=.7)
    ax.set(xlabel=f'PC1 ({pca.explained_variance_ratio_[0]:.1%})',ylabel=f'PC2 ({pca.explained_variance_ratio_[1]:.1%})',title='Bank-quarter observations'); ax.legend(title='Cluster'); fig.tight_layout(); fig.savefig(FIGURES/'pca_scatter.png',dpi=160); plt.close(fig)
    profile.observations.plot.bar(); plt.ylabel('Observations'); plt.tight_layout(); plt.savefig(FIGURES/'cluster_distribution.png',dpi=160); plt.close()
    bank=pd.crosstab(labeled.ma_nh,labeled.cluster)
    ordered=labeled.assign(q=labeled.quy.str[1].astype(int)).sort_values(['ma_nh','nam','q'])
    ordered['previous_cluster']=ordered.groupby('ma_nh').cluster.shift()
    transitions=ordered[ordered.previous_cluster.notna()].groupby(['previous_cluster','cluster']).size().rename('count').reset_index()
    save(table,'k_selection'); save(profile.reset_index(),'cluster_profiles'); save(standardized.reset_index(),'cluster_profiles_standardized'); save(labeled,'cluster_assignments'); save(bank.reset_index(),'bank_cluster_distribution'); save(pd.crosstab([labeled.nam,labeled.quy],labeled.cluster).reset_index(),'cluster_over_time'); save(transitions,'cluster_transitions'); save(variance,'pca_explained_variance'); save(loadings,'pca_loadings')
    return table,chosen,profile,variance,loadings,bank
