import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import json
import re
import os
import sys
import zlib
import base64
from datetime import datetime, timedelta
from collections import defaultdict
import threading

# ───────── 교육청 정보 ─────────
OFFICE_INFO = {
    "B10": {"name": "서울특별시교육청",     "short": "서울"},
    "C10": {"name": "부산광역시교육청",     "short": "부산"},
    "D10": {"name": "대구광역시교육청",     "short": "대구"},
    "E10": {"name": "인천광역시교육청",     "short": "인천"},
    "G10": {"name": "대전광역시교육청",     "short": "대전"},
    "H10": {"name": "울산광역시교육청",     "short": "울산"},
    "I10": {"name": "세종특별자치시교육청", "short": "세종"},
    "J10": {"name": "경기도교육청",         "short": "경기"},
    "K10": {"name": "강원특별자치도교육청", "short": "강원"},
    "M10": {"name": "충청북도교육청",       "short": "충북"},
    "N10": {"name": "충청남도교육청",       "short": "충남"},
    "P10": {"name": "전북특별자치도교육청", "short": "전북"},
    "Q10": {"name": "전라남도교육청",       "short": "전남"},
    "R10": {"name": "경상북도교육청",       "short": "경북"},
    "S10": {"name": "경상남도교육청",       "short": "경남"},
    "T10": {"name": "제주특별자치도교육청", "short": "제주"},
}

# ───────── 학교코드 앞4자리 → 시군 이름 (동일 교육청 내 중복 구분용) ─────────
CODE_PREFIX_CITY = {
    # 부산(C10)
    "7201": "동부", "7211": "서부",
    # 경기(J10)
    "7541": "수원", "7551": "성남",  "7581": "부천",
    "7602": "평택", "7661": "이천",  "7679": "여주",
    # 강원(K10)
    "7812": "춘천", "7822": "강릉",  "7832": "강릉",
    "7842": "동해", "7863": "속초",  "7872": "홍천",
    "7882": "원주", "7922": "철원",  "7952": "인제",
    # 충남(N10)
    "8181": "보령", "8201": "서천",
    # 전남(Q10)
    "8531": "나주", "8561": "담양",  "8591": "고흥",
    "8641": "해남", "8691": "함평",  "8711": "신안",
    # 경북(R10) – 기존 목록에 이미 반영돼 있지만 혹시 모를 경우 대비
    "8911": "청도", "8951": "예천",
    # 경남(S10)
    "9022": "창원", "9051": "진주",  "9071": "통영",
    "9081": "사천", "9091": "김해",  "9101": "밀양",
    "9111": "거제", "9121": "양산",  "9131": "의령",
    "9141": "함안", "9151": "창녕",  "9161": "고성",
    "9171": "남해", "9191": "산청",  "9221": "합천",
}

# ───────── 전국 학교 데이터 (압축 내장) ─────────
_SCHOOL_DATA_B85 = (
    "c-ox3%W_-Gk|p>nWi_fYs{!_V?{SSfdzd{d>tX)~B|$1kq*`KLLI;#cCU`}P)G4YCL_xZcHD&of0`LzV9_|sb2|lpaHA_o7SM-I5"
    "?GfSO;m`l^KmK#m4zfYp{pbJopMTGGet$dt{cXDZ+t>B@@b~w(?jQfpY#@K?|KtDt-vpKAgKD6t)zjH(KDvv#^^XzN<%XJ$S7-a1"
    "koYf3@8;I&D8uEOLvU_glMk{&QLEusaBf}hP_0LemM0VRi)4nGNA0h!k5KM)`JgBxYC9hsebyv;aBf9DD0P&v;~w)xxuHJ2M88N-"
    "MMN$Ce7-zCVz6bxUM<|JG1w|%SASfsPTu0!JWF4?nw+_DH&Kh(@A*z|tUA$8$IEZ?-`~Ek{&>#JwoAWow!a#qyINMWE&A9kdq!5j"
    "#~FOjv{^*0$MfaM9=1Q*fV#nVS~k$rJzjkvRxKN3J=Dz_<>7yK(5mVpcDc8se_j6ASq;xtN7L2MiTn37=lCyv=)s`O2hCmh>gm<;"
    "`au7u{uHwVi}ZtkK3`o7AK!u5AdmE`XU7i0a6o^d=>Nj{@QD9~GX27My4)Qx*eYQsqt$52VC#fET>Sq2W%X{3Us&#*OK{-o$$D$O"
    "x}L9&n9H#%H?Uhr>>R4MH11Dsbyly=)^Dy>i|J~3vmVYK-WB1~j&C>_SQmrJrn;UCx3k63=XIh7?^gF|xj(aCXCmG~l-%Q`qVRj%"
    "bE7lV#gNb$@;0KjFP6-$O7!^LbOP7E+_DmqzpNw5$r(bJ_lDal-@NcI6FqdrG>IPH4255yZ;o$!(7DL-L=S$uQ|B5TWlAWhvOt-k"
    "U?s$Fo-U#w*`kWax9NI}s!5`t7EMHL=bI?BU7`m$AgZa~Y~Q~B{>Ke=^>>M$INCOfh!Ok*$rknJZoVTr?bhizCbR>kmn$BeUKyr0"
    "-(S8SGauC`ir8`@Q3Gl^W?oXthyC>)aGl9}Elc$HD3#x+PDjFD5P8rcDU=A4mPQHp+J9<>_FZz%5-5K`e|Mt$6x|hruq(b_5%0=2"
    "h?MVFs~4vX4+9F`OI;oAvVZI>_YZJxWI98Ka^D4=#4^!?b1Q-l@Q<72(@S)2O%O^B^_n?TRiUW$;Q_&OwS+82a)gP!R4IzM&}D|D"
    "p}y@iC>x8s3JX;=m!D?nCFS-~F^H(`msA}jt<n>7^L+TZ<5mitn_H<Oi>U2$E5f-@dfbjwh(uaGovfxqNQv^2*==u8;E6S@6(vtj"
    "0@Wyr*a?N*0vxKfoj{?4dwD<&r_3$T8EQNwBv_oGd!~K7!Gu_S3qsu20r+DgMm+yagD&o_xdnvo`t}xtV7_g|^&8k^RGRTeP?H5C"
    "*p(r3LIBFa52(-Z+rKpdsHp7+e-OWDPCPu@cqHe@yT%`oEYahmcoWKUI9e|D1dBZD{Jpk(zF3V97!9N~6uyN9cJnTu{}ky*JXAgF"
    "UQN8oaewPac@^ECi`}#3pP!j)S5cS#If<iML(O*>@sb(p`xPczx<pTibVdCnOs}%{yhz{MAynBcTx|~J-e1$7*yDY03xdBx%R+&o"
    "*b~yyX1M%#ioL`erKg+@S!SbfCZ=K#QJ9G-jY3?7VHDgZ<G-jg6s}Oo;uaA_jHO%Rjbq)A;JMyS9woBHDHY~|!G56$TTy=je@b|B"
    "x1!eLqvg*J+oh9m#!!R{vIsKGp=Q5ORAuf?LBaP(7oJECMLdCJ6};Sdb7)qMKR5@3KLuI(1>_XisvQ!~E64xZQ2u(wjZ3wm{(O$9"
    "?q#AU=4KqgRd>HPT162C0ofb2UaKi%_NfDkQ6T;H(5-mr?s2g-9m7`cGF(YL?Di!n<MBKMH3vV*1X(@3Av`;RtrGUx6T<mhrkyNU"
    "@BAfn?4s;rx3k5hrKg9NFYnDzfG-Xnb4QkDnHPFk^A|m*3!~t-Mi%se{kO}L9Z^cRE_55-LHloEg}g}g#Gdy;WB<U38YTjyi73d-"
    "u1llz1gkScF_t~k#_yoS=ma>*Jx~1CU5r+<OY~|Ogm3gH<{SMcyx1cil7cD}wfZ|Fy1hk6P);gt<%0;)BGKcAU8U&7u}By~rS~G@"
    ";*7A;<mRdt)Wr^=6sdT*__>^YX1u_jd+rTBxn#b}qyBtO*m868k7y(kW9c#!VcTiVWw!kD5`Rqju?$7n$BLk~T}@Ue=ftaA*XwFd"
    "!~*4Utoh2lvH`u<v%QWGMud7nef8blBaFgOMHF@?mWdv>iIqCaLKYW!QR@5aYO%b4!{@|SkVh0`D^RPT(&L*ax4Eq+M~n{X#nE32"
    "DvZ#q9}aagVcuxDp-zto!BW~->t{pEC{ZVR;)`@{H>=aHtEX2^5yIEk>=LsHXLr(zKv1Vk2LujaRwM|vk-9`rNW6wcdA2L+Gj6K#"
    "&)ZT_q#waA*6b@`hZLWtU#9Ef@^5Dl_nIcr6La%xbp4CieiFdu5AS>kX^f(Kl!>0ua2i9+hlr+^>m4zFDJH(zj=R|(c{0dNq=(4S"
    "172f)bM@#64(qqST)o?84tQax;|UR1m<=KdTbC-)6LYgKTEBTo80gA8qA<bOCVIlq?dSGmXL&kBPK`$J8a-i@s1>yukC@noMp2wg"
    "OEuLWPsBbztWiLHc+16M3J-f&h=+NiCuXQTe1h*Hk7^={`>rzR#)^fMv>rWi-YXX6dFapk&!K<v<M&ZzsQF8V^K!BzRvfkxcqdmE"
    "Q4BX~L;ZNd7(W|DL0;y<VhM~MkF4`5s9fdm_L-F`6@^C~iz{T%1{7v5vNgJq&})2U%YmVeZ-_JHRaQY=A2RB35m8(~)SyYg(Qx_c"
    "3NqvP>qAl8!EfveHY{cBY)qez*ezSJvEy&_gc7TV>xS@@m8QfB3J(gZ&3eCj_Jmk9;eTN$JpFB8W=utGzx0ExSZqzNeiE-jU0;Vf"
    "Ip4lUL2Md5!GSQ!#ZGi0GpDSIaQ;TFH?Wv?*BA=7_=(fjmVmhRig2i(jpX%#SR-wrN04qWQdhY*Sze5mA1@hk?O8WGBA$munBMS6"
    "EQEw9(#GNf;p$dVgo#zQlZ~|+9uv_=dO>&;6HQdyi&|ZOS^oRW<&UBK_sRLTg=p+YsBpC|tp%=L`ryx8QBZ(o9n>48C)Q3;$D(@>"
    "Yu6ZRI;KQ{m#EzacKg>=;Z|}eM4@WKtv5X8qA5z<$!Dwab0+PpiYO@U%U0IY<6^C<4K=w$Y^S;2T*Is1voRy6n~1`UHf^FOPK0vc"
    "D{+Gt=7JOy6^Pyp4E2dRvxT83wZGE6{gn$2uWW{^(S*2;t1P0p>sWXau=s;Fox#QGj~TYlJr7^(t;RQuX)ZI=yM0JWX!1l)+^Vgi"
    "<|D@F>eu(hYff5LxuNDvdavGD9z`djW@*Ij%8AI9Ceb6Z#ha0h{`!lLaCkVjL3Toq9>2BAoJPsFv=L=-EYM!{d;7&(au?}-IB<F$"
    "V;pD=HNi4NReyMKuzq(Ag(&-YEeUPHzoj&DrJ(TCIpJHaDB|5GXSOgDemi&Jl{A`&Cj#eor>JYri|V7%R=ZQlB_ZT$LNVN^4E2V2"
    "*X!GvLHVfTfuTNKF-GY&prFhSHRBsSzEVDx&!JWm=Fau;b%Ht^Gfw=%P*g}>RRz=(ue0HwV|gD)a6U7h5Rch14tGYFItLc?vf6u%"
    "#Cv-l_UQ3gS(Rqvp=bpcOx**0*N;cbzZT4r)rwjlpED6<T|{9KWmTdl=H`#^yM3Pqiz^0gL~)O=%A(N>i(kZgp}g}M+(_7ls=@B|"
    "aRU+0sD#3<>?YCU&uX=qznkO!GVcZOWBqZp{CB4QkB?Y$+A^2ptg6T#v*qqj>=^dwiMjd1J9)xoi0eh*P$!HpSOvS2>O-QERi=X7"
    "p*|ci=7l<<Fz)r}i4bDHA0{KDrjy@4t<nF*r1j|~H8~?6ytSd;Fb4e6#=<?qZ4<xiY&G3st^i%xGa}Tvu#~RV<Xpmj5VhII1{ghY"
    "`gCQ_A%p)QNCu@RPM@yPIiY??bcC+ar9?X*&pN%u96esapa|Fc;f@#<h%fSda5@+sSyTsQ;QePj-na|FhYp43V0IzsT~I(Sx#vR_"
    "=*NUdTld5J&+G97GHhl&dO|JqC+Pi*su*d?q(cplG1E$u=!s;*fuX>9j4FYZp4e}GZ@-@tkKER(I7)#y_^$M8)Uqgle-(y$J!Wn_"
    "o8jss;{jKBqNv4ab@YAxeve2AbUR9okp34mg%i^B^wg_Egi8OB5wi^}^t8-3M`Tu{O<3B4*==B<*_Mf`m|?9-^w(dsc-@1BwLIJi"
    "j6<pm5m~;T9`pEZ>|53^zB4sU%7}v8SgIQ+J#mjH9}c(#Of`caO(pt>G@+a6uZM+nk|x~LT%1pBC_I;{3pdfxl!)^Yo_PKroi6{n"
    "p`x-a2qyp`ZgdK{gyO4<;I=rr<l?I}ZsF*Xh+cNOlb+n;1@TfA?iGq!O^=8(qWX+S;g&;xxT*-m4p)z!P}l9F2;+u`CjF=z&KIT@"
    ")Dt3~-9N9oh+?jFLlM_{6V%9)ArxHNq`7gyrD_vCIhTu=5>3&_qgZ0S!icy+73weu3Xg5bLTtmyIT2!-g$JNRQSonTHgqVeqE2o+"
    "qzrnwUJ6dm94`oCqduaiW6|7j1z1JRbj*1Tl=BXC%mibrNx{8?hEw8HW<^9n5t91cP<p;3xGxtrNWVZ78LRI_Neaej0!0VOec`v+"
    "Dfc3?@QG6<f>*}MX_T<nkLA?+s|8+b#b48TABYvREp9=G%epq;oH4ZOt>JWF*mLBikWG>+JM3%Wdj0%}Nyly@iZLemKYjd#d+WLw"
    "E&TBp?h*4_vD2koF=afph8Tw`g2$6W$+j<8lt116V17F0Qn~fHcj23BJexofo@&Wa2yv+m42A3VS<syCpyXf12aw2eJK2UF{+{nM"
    "dVUd6kcptxsScMvc9>+VGNPbltD;9w+=lioWIU(e8?#@8cRRBL8DESDE1;n<mP$`JCj6hSiD+TJ2{T3EPoyqp3OE!cKYh7i@q>>K"
    "2%T2-F^|F`<eNlK%&jmK)kMP=<2BDd<&Z7H4(wqe({#}r5i(^riJp+RI?5NqI6nxd!=a`>iJ%}Et}-Bg^*4E(q(l@ztZ0p%3XalC"
    "#G&5Lney)gL*dG{@Iklw7tTATD!Tg<{+P|IcK7PX0U<8Bz>OahYAnk;`!NA+%ekr+zG{}d>$i0j%6t{*Ko1>2X+u+I3FR)$qtne^"
    "HiYzO(oea$i3NjeX_RN_7vx#@xcN5=k%U@Uj5UV$v9$3su^MtDsa$0Xp!wQXijuYq&zR_FRgj#9hDY*?Zc|1S7U$L`dfZCjQR`<%"
    "%h^|XhCiC--v*bW(qngD`h7-|?+k^DUpLmkP?8~wl#B~zH-QX~i0S#;K~PAFocM_biJma~__@895~j28Ok2PBP6SnEme{rapK~al"
    "A+wtQMo;j~kMiavnhWne@<vY_)zVP2UyPDpMHHsw_vne6(I1~TSA=Ojq^7R_?KK(C;JH1XaAtgOC==AHi4@lUG{eqOmQYAVsnU|N"
    "1%gDy2klfM6JA}3q=MQW<+mV+g<QA6cmf^m#<X9f$6xfNq7LO~BhPvN{xW*#;N*#(*f2WE5pk&94dR_sg8Kf&{oiu-nQlDSRq+>A"
    "FZQI4(8XwVJeMwM!x{5Cb^4t@-Y$nDNiP1Uek#w~_*3ig7wLk8$Bx=!5$-ep#I_NMo2W3Gt)N~oPs>hcc<C->#-N=?6muWx3@_#S"
    "Llg#;`ASbj1?$q!m$RM6>J(Mx)0ZNscx+*54c7!UIa_`jLIH0+P<cHW$~Hhkh`sVJ^go_J^txe`o_Nr8isD-Dbv72!47bh0So@M|"
    "Kv=^4Qcf0J?PdSq64Y$M*xU?7*<&-~{6YdvA!%GBdV=Skdxx(%p6l`PC~MJz6#Mce$PD%3HTO;&q!GEdTWk3;eJo^+^ucU~Lg=gX"
    "bxfYVe%Arv$B#Gr;Q<t~n+L5%=?UMi^6h}|`;=CxLs8hSC=$K*friTP@Q5n>^%n?XZahS-(^a16iBqiS>$4O?hE8#r=!umwlv72R"
    "GgU{_Kf(DnUUT{jly9pF56^%FuIwVw6S=YeRKDLMGPW`ciC@1z<#g16p{Q;kxzEd16erm_%NI5*5_nwn=!sj;@00hJcnp<)?0ar}"
    "7(%7nGAkfv^hC)`FKv#`xh!UVv^vxu&zXBXpkSX-9qdKFXZQ5V`Im=Kb!KfJXFGS*`v*~j*aO<3KBK6@Vt71i4x%bI!+c<<SLf(h"
    "QtBWx)a^8)f4Og02z{9+dT?%CmiTZxd-vW^gkBp0Dm~0M^#)4J%$?c@51|_AKi>w_3?0ioDY7uuXtJGeO{dNgqX$Q+LdR!^x^tQy"
    "<aROWtk=1eZ{3hx|MGzBs>-aa@`$=yQ|@2x(-!L1JPwM2=<6)e<6qR+eptPqgJ0yhr{Us?+P+4PzRnXpep<UQx05UUi`pun{=SEP"
    "QEsUjio(aL3p;&x%Y;5ORwMO^yND8V$_Xk}Jhn{O+Yj4&neQQ0gh2G+XxzP?9-Npv?cvzojYxlRiJgcr20r=y4c)X&m05S!*@(Dk"
    "M2OV^^#d12VX;QbUHHmyTh|WAXnAplAFEt@-FnpaBQNw#q6dy)xRN|Q$bry4Kv4f{`xPVfb|raw{IVF>>TKlpJ}CBWmyYf}g&zEt"
    "Hq-Dqhaz^VdsXK8MQ>NfH@;H((e@eow`fFdU(GJp02QMLeqV#Hj2=Fxn#(Du>3F*|aP&o&=)qCkS<`OCv+>=sfsd(7Wnrj0A-<0("
    "kS5>88|I7q`Bq1@WQ^||`Jyn&M(*eRd@G__JHDIy`6%CXO^<$mpJAi4i5?uKj!NJWu9$gLWhi(j_^aRVgs=0vKF7yy6IHanF78Gd"
    "Jt%eEy`Wv)uXmQa@NME`f;TY<YId+X8ZyG9QXtMocQq8=W%>L1ml)Eo_asH-VVBB-TBTeuRquCxttL-k>_EM8hP}_b^vJkctI)9X"
    "oxAa+kBr;3UBZ6<;smK=0zM;VUU@5`{(^Kb{qs5T)hfmn`z8kP+=`ZW|0tHj-LuuJ@2eMkkF%m|t6M+lLyRQIO}mXd2|pgLuIKAN"
    "CibVE{O`L_<c;Yq#_^}52*7kKQMC%Z*zp;iU+#y?!=(3Ve_qN?mLl8K$_~2Tu2^2(EYBx6w(YOWk0;d7O_^!NrNURwMyvOWP1LRL"
    "&5Aa$%N-ndg4VAV%$Fv1Nm{|PCoHe3x;Np;Xf>MRC#d$;=79BW$X@KN4~Fg&Rv#``@8-mZ^!awUkTV6t<<-;l*tkta@x!%={^YHk"
    "6zN;Xu})(k?MJTXck{|0VO`Or39R4D-BWt~{51h@6X)-BLqEpq&Q8bjubcnl|H5&aJF7TC%GL?B{5f2Ga_^6k+v(^p)ZwM*f8nk#"
    "=zjZ99qdVp+NywLK`nChz++S%e7W6zh;_$v&*rllkI;SHSuBjA5LG&U^<5|SW0r>6PS5Ii=P_|57R2!T#}iyrsI%}D$LP-SPwFb7"
    "@NcOCO58s8+2$YPb~w-xi>$1Mb-3&IZWYD{cXb<#6W=zY0PY_pDtAgxm<nuecfALXDU!Ng4mHA8d60z}$_-E5B=U8Y{^@Ro=Euw@"
    "-rp;z#f;%eYtwi=CTw^raXre1x{PskKKCAb{qW_}i8Qv_dPlXvj{eP8!F<0UY&Hpq9yiBK4YpF$c7Z9(FB3iSG7hNuOTunZ*tDIB"
    "v2;h^=LZ67n|Zns@^C-f<#pI4dSaA>(r8EKJz57WA?VsBeAly=xCvj2E-Pxg*m3lAo#+XtmhGjDM5z0(EupUyJud2-fO@x2sESpd"
    "P;=_ZJLvSut62Z+BNU+^1f)cz(>I^a@HrP*y@6#;T$Ql1uXn3tJ%ZKBNs5)C%TH&R12D~2BD{_X`B12mso2SxFB7%R;wY$m6NT@h"
    "-hTKeULN80_we_hadWI3;jT9{t{O?frXGi-)WjErOXZ;1MB(d_4-$5I1X*_Tp0v4LE%o7@(<XX+msV-d_~_a>b2`$g6s-?;y-I%3"
    ";1(9PCd#gh{5&~eRN^|K2+vOz_%kJxtD*~I-L9takUmfZ{o!t+?PFH_##FeC?1~4i_*s+a3C~aX7R0hHo}V(&69&=1fjR21l`o28"
    "&G#@4w22;^TN%71-=>7WC{&P@Uc@Im7~iTykIyYD3^kizI!T-8iBXi#r{a@=M(Gkg;r9qA;^~y-ML<o*xGq=pP>iczW%8MpVPI?#"
    "T_1><BdS{vTqU+c@m);FTMtEyy;6Eu#O3xn{x0oe&?u@dx9#d{t1u2&Z!2gM7PWwN7AD|PQmf{}Tg>8AMHFQT@!!}a?9t`&&(DC("
    "t;<bK?V(`Kly=;1R79_EL#*(p=wr9eGuU2k2=Ojom-xAUF-4-E{4?2q*PMwZEW?9nzO(%E5}%=6^bU2kAVOCH3R3Sy3272Np=K9`"
    "f*)&sWvht7RyI%c#HqA3x?2(L!HZig#!W;)7UnFCf?o|<;!&KF-`_G<LmpAcWmn`~qKB{4QpLMRNfyfpy1t99+eG0nrq)IzY^`0m"
    "O*{&_w(3NW8wZLo%Ih(%(r1D58*M8dzUkUTkDtEM_QT!2vX6vunPTQqSaf8d|MU_I<0=z9ep)L#5rogY3qc=>qPW)u16{!4wsene"
    "BbL}sT@)7{cqa$wQT}8J_~Qw4OsYN*io(tZw;=e}<!O?46I&mR6HjY_#fdkGp5S5F$yW=8flWkV+{+U^Y+TI(&xsiJI&CK+B+Y5M"
    "MHWzBmw!82e!6+YKj>rFn@Eov&*L2jMaql0xDE7Qm{G#F9Ag;<d6DP|%`I?%GY5saeY|1(l}$nsx7%$Ld@ek;jac{8!UL;4wo6!v"
    "CO&1tkQ0BTo%QL}WBbsl>Rp-WUl0#uAC8*%gT#_FZJp?umrEV8!6J71+GT@8Pkd2Ywe|jDdA=Z4Eeo92&@Eh5D{Rp9vmx#!$p-d;"
    ">!S(oyVNc^QVk2fDC<yyT2O$vu0y##qlfv>Xkv=fb;sxzNl4}(p|;Ph4LJcyk2}y+Ir)Ai;pdRgw@&m#<gD`T>TW{kV;6mAV@X*B"
    "#C7W+ZF37kT=!)FUJ>zM`Z)C{F4QE{m+E7o9jI5oq9FP#(c{s_RT$;31><GN4aIo&GtHa%eg!SD)WWbYx|^{3n0yG_-blKAc%L_k"
    "p0F_6en67RguWRhdR%Jdfnyh_jlCI!aHH=tB7CR~;X{IA(%tk)>rhTkZuLtRQL4;1xf)P+`}IAz6I$y*q$sz&mnRbo-+ow~kbo#V"
    "M>FE7B58kxp-$c|4-VXVt%nOPpg3IwGekuAsSXl7kq@eeceZ|W_5b`cVVYuYZsSj&a<H@_+lrD3u46*g&hj+kYL^KDD}y4d*ms1o"
    "?y+6M-q#)PQAIW}no|}-VYG<d?u`p)9?w1Ts4SwytNoPWs=A1NJP~;T%`i{&#BJ@R(vQ8njUFD2e5xY~lg?S9$4&5>RPqnVDC`Z^"
    "MWV+IuX;cIW3$fWL*G)We*BLkJVn<BnR^cW<AyM_Ns_q#qQwpor6;izeyqjlZuySKe3^RF2<nv3y)@m)qqcLe3Q;VMe!dTxXjKF&"
    "J#L`U$NU}C>U6f8{_I!Fe^fcB?MGlcejRN?i+jp4KNh+XQLwY$KWqv^AvWSR*vOO~k6<ps-2S|ja9cw6wS9>1UXQX#5?P{c2t;<M"
    "-6^4GclK#StfX7w#`e7A=^*J7d6wvL`Cr=3M{;t#{4Wwce(EdR<anHol$98C5ru8M9zA|20^inqSTs-3CVFD$7~j_K&KXpg+aVD>"
    "W)_*n3~~?4JFraj#3-4ekVF?5rAqXKnN`o}Y<+yrSeM#}A~Jt99`5Ik=)+j?6L;rUYGYEAJ{8<I!l@K8ZrdBzy~bhbCs@@^70bv#"
    "KW>`&^67+&0@VGiSf32bV9SWbpJy^*eF`ejJs$vNz~6dRA0@Sy@u?1aSUA6^DSId~K-quhAi<A!q#i7=548xMp?thA6VcdXEWpyN"
    "NHdhmx>`AEYix}G%X@&xh-&xT0K$rK)t|7BU?7&Gs5h|axNTgNJ>kRq1(r5e+=AeqKQ&wbdgiVeD5<t}Z(ILq|1tW#*lzccKoI?$"
    "{}_R_q(l_^E6j-(=(JX5Vl#Roj;d7Da&&;7Zmqp(`CVJ*79ONV4_}m}zg7hG@lvw#kLOTH7O!Y|)QpgjRY3hDqAIl`hFk$uno6bI"
    "JCuA~BImGE)auzW`b4d)MwX(8EWV;P6cB&u_nz+6OCs`bU`87$yzqI>pz?cBlJoO=3_TtPrj5&w0RAw47;R7qL_jPmUbhkY(FBTN"
    "6(dZ33xZpRTl*Fw+_1>XyoxBo6JJ>qr374zDED^J)P4AJ_l!snb4qPj-GxJSw|x2TO(5V{(u#JQK-h<o+p!Js*JE+g<1UaQy9JjL"
    "C<Ht&$_==bL<88RMc#VALuy=2XixCJ7I>nXhc~z2v#*4w&3$!!Yl~VMEwV}KyboMG`>=#<bbi{m_Ly7fB_2;xnMt7!$KT@~erv0E"
    "OA7_Rwc?zopt7bRx8ShT&cko5`0B#}5h&&st|>R*<deL&?$DFGC&X~4X%jdMCv<rifC&)almw2p3Ad#5#bC0#<2DfBR#p^dJ6b-S"
    "<31^05<>Ut916EBt(%_F6J=?0LphaubWOZ^a@~#d)r+^d(@K*w6@{4u%S2C{6k|A*I65%>)(d~!*qa3uVC1Yqkx!#1%1E|`Lec`W"
    "_%fOk=E^#u){~?4;SOP7*B$=sB_R*<zzT=LYh4yuUU^nLU&xbZ>xCtPs8M>{1|=46Ux{n^{3n)b60~2X$NAPN>IU*XNnr`ku~!pR"
    "OK~s6IzZ->E3HzL1_<JhDfNa&Aa){(TM%6As}A$(obdPM;lO$nl!abZiJqtc+!|`JV7%=%7Uco&eAuX<@N^Ej(2Iz|F7!6h<IY4C"
    "DX-3nSQ$wQ3aH&P$abWXMCp;Fqq6t=xW}Zh{f2uP{KG%Y4Suou+Pt==M78R|e9i9tMQMh`z)<qc<cy#02(}3eKT!+a6^i=xOeXwu"
    "h`c@u@6lEuSNcb=dBjT8_#7KimAyU+co7#qPU{v5pJ$e^_qIxWm^qt3X3)BaJ(9v($cQTK`zVMx)h3FlJQA>o=Rzbyo#=^5HxY%W"
    "1e*gwP?JkUq8447=y8*88Bk8101AL6SQ<Srt1_+*VPSJxSs77}*Ep@?(Kx!q{q=d4M-<XFB9Hs|=o0boYZ|}N<5Jqb<r4H#d2L78"
    "dr74KRaTu?P<uN>ICW>J)w2l`P+=eCrp;uo4k8LG@tp^HsCa}~>36RXx$Pb9xzPi{(|dVzU9RxUU0#~{p56UUghZF&eY*P-ecG#~"
    "QRxX=igN5HQO2mWE_i|hgLaBC(G&Z*F%<qj%`E!a9RVo=ig@RJZky15`vKAG<)ZX>F#RB)kbuBJ*!fCNJSaLv;c}yi&r*lNt6OGP"
    "Wk66&rg766AEdrFUc@SJLrRMy^(ItxS9*{S(b?pLC-V%^zLOp`Wu6IHKz+p-*o4+v3S=5`*`W|)I8q3vvc>gLF4!{lHWD74=-(sZ"
    "i^fAHYPt=m5nSTAGm)YwC^e!A^f$Qnr4`x*g`2f2ryUiBLN3SB!eTxB0Tw*aCVD~$n@FKbDz|yqZx=g6)LdRf6y`3k6FpG^IPB8v"
    "FHA8S`y#yEmG@tF5rx<s>~*k5^q-P7s%^h<nVgNC1){#2ScJk1Ckw1aU7P5M5;nF*zGp6OwW}fuv)VO@9=FGat6X9`0a;q>9*_zz"
    "XjZe2tSBQ2DsZ6RuJl9@NTVpc2%7k+)W#*KL*@k83~?)v_i*JAg<buD9?!#+`z|xoi#;NQLnXFHLAkY6ndphT+tvv3G89?ia|DDQ"
    "Zi^!}lP-MA@s9XGj)zEnSi6Niim=agRYai{AwiX!C_<jZuOkZeY7urtVe+I$4=d7H7P+xtG8qFmfP60RHK-FkUShAYla5!J^irjZ"
    "C`fkYX%xc4-rC-ifNH1^Mv>@=`rY;|?v^AtkmnJFc>lG*u|*|8-%=)eqA*7o1+Tj#?Ts2mEnmE5WMdssm~2d=F#9tz)b3CGPRZ*g"
    "qOgeQI?)sLs%(vjXZ65x^#!$$*R{{G+E!KqgWoR*v7a}6AS8$L`WA$+gLMY{bi-^~8;<L7T-(N2?Orh!0GlC^DA!sVrl9aPe{Haz"
    "NWU|tR#X|j3l;lKq9?d#n^5vN@Q*5kZ_xoSn8=X0#CV17uJ>uzhr}y8oP9AW0;YJ=43!=TRIu=JrH9{Q<-lYGa$k7*JkjGXKJ^N{"
    "c}^A@)6KBAyciKN9(Di)#T+G_;UN<XJ?J!jz@gxVjDC|>hWd_G#!-Kt(i3y*0_ux@q5By7r&r7C1O1<3qI6f@<jHDyjF-+RTiq~+"
    "cvVwhPqvOI%nVo<{r+3L{IoAPSoeYQz3!>F^+6%mUwI4o;*@Zj3@n*F!FP#r{2t!kg2M@SbyeL0k~w$2-0JNQrwV-xLN-AUzFq59"
    "6Lf^&**b056&FMe)-tZ_?DM0}-$9#)-=7f$n=Ep}qmaBX^Lr{iAab*K;$~lo9aV&H`8H>sHsM<ke}`O!ZKB76B!d84J^ccOD2ELr"
    "^h5??9#AvJM37MH@q9HolLBo(EJt{E93pkQs%RB=^hAbHbqhi`+H5o6{t+L+7*KE<Nbjm{B8rJ<4NDAkYw$H9ibRjsqcAP;knoSx"
    "@jZ2j*O!nG^e(LL2Vd&({fyBN0+uMhJ_t{$L!SYyeU@PlNZeXPg(xR2jGs*1%t6=G3B`0KllY$?Y#ny_=VvfFw6y0{4@LOYiim}>"
    "(W^8TcbU4eicKuzAF2A-?f#KGOZ0erSCCo`WhvoE3*$O`*B%vBl|>X1Ri)kXj2@|)Qk01v_Wx?l3PJt93naoV8-(3H#v+;H4j&&f"
    "N=}&7Wcav}lZAVV@NhYa)C?jD`-&pb<6oh?-G95Bjzj_eV@5=bs|Mb~B0h^;t$$7tm2fgbX3Bok^k;`fI?PE`pC-}cz0LA43e`nS"
    "&*}aF9+Kyq3>j)Q9a`r+V#F?CiMo^i47!0Pm&7fguO5#=s&-nurP2d-SBtRyxLE!iN^MCbkw=w;ixKY7^x>w3p*|9yZ`o}g#kk#D"
    "L%~LP|6P@$$mXNDp<vsB7cyByL57juC=4IEfcnaGOc@yJ#VJuiWspS_b)oxszdB*@_}DUh-3eSastmD<9tDN;<XNI8o*`irSVZ`1"
    "I`H9QhcVJBABd8e-h5OT>IGGUC5(lq-qcn;UQko4n@-mydYlh>eOw$9!B<YPSEJCyF<v0o_gET46!c_PqpQ**r9tg99pgn}eL+!O"
    "(=)uzq`!7`*PY>o3nZbVHWXAMybOV47eq-4pVeC#>cuG*ot_&#639`yLlA!d52~BH+cp9CfoK30gvl9f25AyKkvL#XAl|BFD5T?2"
    "*xcGgkL$gieUa2iRNL=#y!<vNc&M*V{RL#6Cg{!(zmNZ}F45!O;Ub_8cbMGICZe!NzcdOHMjkkTzfejmi6$MS@ba^Dh~{-D*dy=T"
    "AZ3O+XFLL`!#fn-4l4Rj|9lSBf)+kBi5|Zw!zk3-w$eO4hkEpF>(v<Lvt&F$we|GW{CSC_tNXHPZK4N$Ki8eC^mu+>TLl!c$L#&<"
    "Q2SeQ+_Lx;$G@2B_eDfu6+fCpk1OY@BK~;^`lGE9g3=Q;tQ7V6_v|gv-k?Y*CT}8F6k&DDtp|p5r5$4t#TuTW^tf$P_srE?lpG{m"
    "v*^(ieuPp{M9N+s{39L(aX@3ym7b8y`b7((BZF9eGDR(CN04Q5P$znVZ<V5m?DaNOknkwTJl=+K5D`KYNKZ3_x-b?&q4E&19>4oe"
    "7~Jw=0}EY<dTbTNl!x^n*qbfH$tKam$1qn9uS4w~Aqr344iY`_N)4<0fvLBjhq>V|{VFIt4mBNPhu01iQSmGf2{l&>sz`XHm-5xk"
    "^5+MuXbNTQ77+!dc-xt}v6{4mMDo-7Yr)m)(}$#%>4Tnxh0-IMj~rVy2>j(X_SNs1dz<XwrOYg1yoZHmsD6+>iik=r5*D9l-9*&#"
    "WFM+kn<oh8uoG<8#{vvVAH{5^)=+rqr&xyQFG5y`qg=0pzito}QRwvvru4)kA~O^o4<j)rdO&Vg!vzv^k~dYN$7PFJPG$#Cb*Z|u"
    "Isk5a?_NP^q<N1XciL)F?Q9~Qy&zvkt@OBE-5Y-zL%|ku|JZLM3Ue%`QHaOB?q`QW>N$vUpiK1e9<vkbP!~IlXF*X%c%d+V*6N7D"
    "O2Ac#o_L0IibC`s-<z#8`tit}0!c@joKbD${FdnAk6>G(P4sw{M6075OWqk$g+rX|O@uu5#4bZv_3Ugp`vO*sm*<r#{IkzusYXil"
    "s7zCOLbmJNJ~N5c?he<n+)LzwXklnFK~QMrd<o=eH&Jj%zv*d;J-%52u6aM=ppU{!9{DznS;T^syF6#oh!A~|_z!(ikvPwMOMVM="
    "dW?NbS}&<O3%d;bh=U$>E`_k5^~yF;geIT|e<p?9klwTcDQ-as@41ad1{~U2OK?76E>P50JY7O0yqaV^3VW#)iJo|#G=_pp|9RtH"
    "7z;Kxc_Xlmh3M7Zmz^hig4<yfJi;Llt}c&)e7?mX(0?V8j;k=Y7pF|paY8YCXbpuIY{`2(-<@K+u1xfV%P(+me83a~sUr$AL6?ah"
    "&t>S3((i&XnuzZY=z`(1Py-v`&JmvZMMPoDuM#~`*&u8uxEg@pPMx9N&k5f|nMV}ln+QUW=w>bD!OMuU*jHeztjso1MDZ@$BuMP2"
    "FWyxqdLo=4jDq-rV;vi%C%QWNxm^#Je>?jPo56hqi)Y~VhzL!uLjdaa-tvMdY-=SEuJ;(bM`zCW>jR`@il1AV=!quc`b7us`A?*r"
    "w_QYGDd#<U!V%yP`}J7(hPkS}VDTI8`j?pHiI<2U>)TMvS`w{iG`uhXp?)HIgG30@Zbtp25rP{nGXqL51|nv%izp~&vK=IP+<uaW"
    "Q7(=#`$?7PaTj(LM)~;xeKorsUfQxsRpAq;U#i79M+i}QUiaSqYWkKiXs9#SqacGu(WA#Ly_zNWZT_2aGPauW_iet!+a^j5V;NDH"
    "j+7;OqD^O*+b5>9l-gjw&8djxT5S&B=6Jyw|6O@RF)I~N*GwV(+;~V7f|D`=bwnYTd)^y`NS`-3`JH-0b!9-oJooBH5m8L(u-s61"
    "8buZqs&5OV6}6Xpb)qLi(HcWBp$nO+ZSx^0D!qx`Z}R!e<?fsjUs*(9;;Tnb99x?kQ36FW5GzAD!GaeGXhYAM0EC?Tx?Lj#zu8rd"
    "m%_8BL^mSUU_Huwi^y|B&u<?^oZ^6;?-SauTJV1CNOc`Z`>hf^Zf9u1D1Sa@iue@~1!=z;B>aPE>s*FsnnTTwFpE=>=m|dC>OgLh"
    "D&+G2*rA^7Rb#8OdjFa6Ml}(IW%L(`p71b+FT%si+t9(sqnHL~rJ;_o=EYTyo){%?8_=WtC_Q@O?1Y^IOGt;x;};2vNR6ywVI_}+"
    "O1`wgXc-}d)M^uuX~^!eUBYUqPh#zQ6Ml1uMrgMovM~Y?NRY7xAtu@Tz;G!5!)2Q&e8f8MV+o&Z8=MgV3)Q)8gF@Ix5l5px+b6^h"
    "uggA=;ZGHTtEV?qMXb8FU02VZEKiRgb3?bmz@qecZTU8Y6D#n=DIslS&~z@u+WC>frlYaiof1naUdXf!sP3hH<MpuaAOle%ezx5v"
    "ir9F!M?7I}w7lHFLbGiKJ=7QOQ1@;Sxkjn|koPwH@eShf@gtU-D44f-)!X(ykxB$Rb$|850<A^&SJq)Ets}4dSm4s^(G$fY(kWX{"
    "j+`F;h#2ursO>}(HUZh;wu0^yGp!tSw>)8*47wMpj^)d-UjO1;PNwlPrCh75Fb&qDzF$eGBvRMT?r}l+_5nkt;d>f!H6G%oZ_(<t"
    "7?ENpPej$BWR7sDPQSpEweb$7rjG?2OldWVeEETWqqI^5*1}>EevF8?yDBPgBS@91;&neF<ZTr%?h$8K)Od-X!{x_QEV`gaPc&5w"
    "sQF9Wh-CIRk7C}uhJxY`>kzrB^n`t;Gt?9=wOxcZC?18qdCNqP$4BX{{qqCb#7)8{+Xz7lq<Bbo3$m5f0;z66@Em!)A8{9t1TgEe"
    "ez1gez;mZj84}6=>YOk_dJ~^j4JC?!+gNy!H<4HVR#g-cQRdIAps13?xuRx-6e>;6l-w@l313<=rqSccblyYlQFEw_QdcH=coc1h"
    "D5$@kK`ugHYr^Q^IJexl1`rfeoX1~AfeGIhOx#NmQCQqdmgtE?ksAtr=X%#zr6{Twl@|UL6dal3H=cdh>UhGq;cQC~U5q7QwK3EL"
    "3-s;UL=T0w=7}EXcBMz}Mx-$wqg5A%!s}ND)2O1L1k5_jZO(X|@;0Kd>s9yL4bk<W%Y%r!p~8AgU&2>Ve=RhM0J_DBK}0cuOpT#n"
    "#mS#p`>xfqCrk^=&QM4V+uAZOjGjo_v@ar3c;t(W=c~~dsLFKNBzjmCECaXkG-0W{8ulJrdDUOC35&Uy+eA;ux-iPeUqsJ>TxHRX"
    "NJyw>L6hi#q@=6}zfZ|J-F45N{GN@lCs?EO*5Z(`#suJ-A!f6x6FuQ^i=!MeHo!Kbu(_pCn3qvNogOn?Q>%!=wse>1iAz5>)cKSM"
    "sf}~Pvx@Q_>hqkjq7Mx9*MiaTOG9x2-*`xLtC6wnyD0l=<*mVjg5Ntne$~E<@ZMJDz)}=y>#od?U?_aO+QC1AYQk7dvF<vn1L}r3"
    "^<6|^r@lu|@FA=(-b^R73l!8f)5W+7y8>x*BZa5hL{F$3h9b(cRp#IEsD0ujR<?`qveI?P=M~hy0nr^HN6hH)s)hqQ@1n9oahpw|"
    "$McUeTT{Gsoxj$*h{ER9CVD(l-Q>wg3S|&^{mShTSa7~lD~-|<nTZ2KUA*0{Zq-pg84)=SVoVDtAX8Q7?d*7Ze5YlB13y17g}HR+"
    "j8-oWh;q;-c?1Q0k=@H9Ja1HVp&sh-66>Yy<k9NgW1cnPQl*l1g0G-|c6EmO^O7h5-B@C^1FlZ45Pe>&kgcA5SboE77pl)cJ0=d7"
    "2uwpEHQPOXk?8Sl??W0^!z1wz5(2YP6ww{BGFQ8xa0gap6$u1|yJNcWesm~UHT43jG!(96inSz+g}3_=OOAaPl<X-=X`Seaa@n?0"
    "O#HApBLv0t8Yr_eq9B2jr%|B74qcV#@i+b;pnxn$Zxd(|Jz+Bp-~N6f_JpHTA_J?-Hn52Ouxi4H@WVk)Q!$7rNS)|<^hAH>FgLtU"
    "ana-abW9i?r8H<Afk=j(`6HAb+(?B*O$+Mp+oPt1Ud=>GkF%}|-vURaia;*%h{BdNOZ0eS&>)J5S4LrV6dj6asZ)fv$sLrqw?-2v"
    "6Wl$EN;~^ph)!$FT#x5O9n?V=QHWL$C9}{IbF+oR9}#l%=7WfW3<XUZg?Y3_)B<yi7KxsCs_4cz{{8I-(<D)M!ZBf!mx87?7LwI2"
    "DyT`<W6Io=Wx1i=&oE7(N%Vv!5WWSEt!=aPMPTS%n<sk0;MTGz-<L;E+%fUg&4TtWs0Cz(t$Osh&qzIJ!|8JOlF=k<LotCCt(qeo"
    ">c<Xaj;<pL<3pC{@i2y3&)rniKV+25z6JIB=qpL-@n9P}3)A&Gs)UZBeDez^p{YvrM9*$rmousnPmrZ&t1%PMTj-j81v4PDq?OU*"
    "fj}lhzW$!?KVE}9Xu@CdHp>2XODM?iQ&}`}f)H=mG6A*K2#z&{&||gWFf`RFp|p}MG21#}@pO#JBL5XA`W`gT<`#qqZb>Y4{3KM4"
    "(7nsBzD5v(?Gko(ikBm<LV^8=B{DKX+jqlK85!=%tJ78&zt3pGh=}SI_Jr{_<>dwzd7?IT+VFG_?ob}V;Kw_-tgfo4hj{GCIgxKw"
    "S>m~2-HtkW%V6ssmgp5&RZ$=Qs)2<os#;NA^|8Qd?ePaMGE=3mTR-1hKe<{yUr>ciy&X6Wy`CIxsT%6`e396)K0J^b)P#pCoN*>I"
    "w93N?#hb+x!Dr`C-{x$#MHla*Z{HbXP8Lzvt3OZlc!ec1+kPd=hUZSjDk5sTF;HwcO`=DtB=u%RJT%&fnla|?@GV2gx{{lr@+*E1"
    "`Y*}?>X;E4w(E!|XP%Bf72!~Z{kGb@dMr08i;vB(P*#3s+2}@3WNZc0<1$3dvtf5J0c=%JM@5WNt;Z_M6*VlhpToCInGDS$tm8*4"
    "@*!L?ME<GV<AHk@JA`z~%7}ubQ`seYVs3WU@ScqRnb}4Zwm-{6PiS0rU9Kk!rm##IQII((s7bhi!dDs6HC?!?iU`XzX|rG+fKe%O"
    "8X!?0Oe?P{3TbB?3_A;`PPo{myF^d)Nzt9Nz{~jf?4I0E=M$&{X80DNM=H#lb8taaIhKw&RYV~>tu*)Of~ayV?X)sO;qiV>)im??"
    "Vl^HzZa7<0qN!FLJv&%m9&ub|iJquG98iCMPRuRr9K`G7zoky}cy749)L!f@PbQ4ZqlhTT<)QJSN>Au2rJ*i}nuMAmD5yW5(^<W$"
    "i@w++G+wu3+ajW*Rw^Wd>RS-v-cMs;_kNk^iP{mFp~h6;immeM{Q(nQ8BkOWANAzE*jta$eJjBsgM@;TI`cZw<AE!M@f?lZ>xx8A"
    "v|hE7i+B5KLhkwM#aqPi>l3N+M30Z6If*Y0h|0$9<*1(D7YCLth=ly9wZ}pJ*A3QUsY>*CtkfWkf;2l5MXpHnkYBG$^hBVweGBt+"
    "k{6ny)<YsWS4+_<it%XZW;><42DNR`Q=;&%6FyxRQDAvMFMR5R!rM2P$T~&Jy}G#t?wvwy)MUR6jQ$fCA5|xM;-bs~>IQ!ZWJMQI"
    "OhJ;|P=7sIT%`y}B98J0(d?tHZAFOQpzhq+HFrw1r>xVimXIwxtR;>G8(w_1{K8Pw8Lz_(;XVjH`)m+Vi0sYsD$zqNx7tLH`?v?T"
    "w~1l`S#Z;M)b?vG3s!Wc$HSu1+_1=>qDb^abd8-I$ZuGNz-*-__GcIc&!eoY>V=@DOuSH#y2LZ849OP`1?Oyfr8J;^5ar0quz%Li"
    "s1hhuL_x2BaJq>Axjf$cr<6&mY)$^)@nh1$&s15)IV%yW;k$72R~90UJPI?-Rf!&V1cZG~HOaM=8cm4awM|Ij8BG{p+rWY?1;v=1"
    "^{L`fkRMQW7^TNG;UdiK`C@fE#468(i6OZ{Lf<5MoM{@a>`<Ssn1Uf?L}3L(@<dO}EmM?_pTQI1>xhDaDgy_IKu6iw#sQ+YTA3A<"
    "t&v#UsCq}Dc9sc?mlP=bD6*u0+6olA7*REUiZ<(GDNB1^R}m}uGS7~Ev2Mm`F0AhT$nF_b_)Dgp*d^x(clMQ5ZqBe5XSkg7n>Mjp"
    "6nMabT^4zSNIKHvp<-ng#iOU^!vE4qbXaN7#&mY;dh;ahicQ@cmyL%ht)#QTwcIGc*tY92%AA<o-m?f;`-LNDT(|ei9;4h#98MXi"
    "qQxL!0io9$3x6LKJ%0Y267F4T>6>^WR>9->`uS_Zvz&*+b$r9z1zkj;QCMYAs1$|J*F~bovt!~Hojhl1*N5BfBa!c)#SQrpIs#@{"
    "9Ze|zwb>y(3hmNc1&_Q(VOHNd(GxL~aTF|}qpcG?5iJu&x&A_^{Xr{OKRYHmb_Kn~p_r^~TO*|Gn9tho5<TMStBOQV+!1;f4)Oiw"
    "&uJD>n9wT{JuLLB!p7(e-kH?b^(`X`suO4rgll^szzb?lw9)kn&Mfx!u{xsG<N5Lk$Un`jO!Vs274e#DL-C(iKXJDEfD_M<U8pg="
    "pIejY@lo_R>>lAkl3o?B73CCoqKSEHUnDV^PbcEih3fugn<&I$rd!>kFbi9i=!qJJ;fs#X!6LD~6m7AILTUo2cHKu2c9lWG!YW7G"
    "r4g5}&hhfje$VF{Sm+xE*(M6Nsg}JF-wYYO&V6Z{u>R%3d}*<Ph4x!nZKCim&C|Mwbj6jf(2&Bg9}b9&ND0R1VKurQ%37^AQN(N$"
    "Z&xShM0LA11Vkwok^nuf5|U7*?)3L;#DrlN5rwIIX%wPUum&yYb9L(|O$aBZp0`q3JbcSy2E8s-u@rj3#+yZsEg&0jR%D4DZv|*4"
    "YbqDbtH-O;WThJIZxjC)H~as3zl&1Jo#p{?Nto^9q+Xq4alv(>C!%R=i!n79Gs}Ar)FIL3tSlpn2?_{f?K5#Jm2DiZFl`xDYW5ZC"
    "_E|KM9?Y1}i~JUZs0tRo2<{u;>qwOm1vxgeCeaf~%wg}rPWU=q-BYU5Y}VL*Agtp~T!qsCTgS^pPYA_;0<sx=8GtO&<1e#;tr707"
    "_ls0U6ml&DRc=bS-^<|Obtu?BP<MH*Mly$bPxPHA;u_&Gym>kih{@2))h5vsj_$BanXXn{L>=Eqr;AUc<?d+p>J0xn3ryIB(&BwC"
    "MUS3nq!xH`0{15B@+ki$&vGm0rN}`Vg>m3_hGMcqx;&upYC5r$yGLQlW}WB>2Y%QUcr_j2wxN(>(w^Hrdg8p>7p?#8HFKvMx0$+_"
    "PVz_85fNlz&lf=<e8{Rmk68X3ebDYG%U{--#3Q<Um7xy_+1bzhnY&k%|Ef|`+3uCEpo3dy^N51H_hzuUB61nUZdw_N>SSwAy(`FB"
    "6suS%JzfIej6+wr>rCvRCP@T^HPbE<J$}!sp0@XzsH-ZHp)=I<CsAunPpj{=#sq$5hWa#otoCOU`q+#ye@pakIeMm=c%k_&<KgOf"
    "E@orEbx`P|Kp=$kzg55em}sZwlc5I@g()*#q9=krY;McvO#Gc%FC6M4Q~RV1sEfCZIL!=oJ;p7anYyi<?)`N3dp4G60s>nkED@H{"
    "_E1DvinrN!2|M4%`?UCD)x&=OvYH<KGwNlQ<#`o<N9-R!)`drv3AK9#WkqBmVMS5Wdg6fD54{nctYg-w>#~GBI1uOg@nU(kz|F%x"
    "uYHhy1Zx~EsQL~Hcj?q=+C({l%sNg7AXAY}!u0#tuV^G@omPh`Y~!)%-1*y|Vo}<?RNWL`;jd2Eiy^Lnc`l_>@B7Z}G2=D~d;JAh"
    "ll=Gg<_x3qJaJe`PQExm)-><U(@+F|%3D~#K;h$mvrQDvnVxKsO^ZjqXQ3aCVh<09nDj2x{&ZNRR#q3{o0OhVkHfm-CNe?AvA$9P"
    "YfWsw(8EF%ln1>Lp^D3Gq9?c!P<VDr;TS*Yp_l;DIy9M7?0jc6eomMWi!x$~Fz`C`qEX=MG4UF$L&<Q(;$hTvs4%L)A3KB@Q;el`"
    "AB*_w{D|!)3LmjcBT5zj?MX{rI_wUDoY^{LXGRD<y)tb%uFhN?QqvSm)ru2kDeW9CQdR8g%?1{V;ca^hF&V8!Q%3RbjmXBv)*+um"
    ";Z*H3*$h=53+#m6Sh#VucaZfaeas<Qhg=h-cX!#C$WzJU9s2$=l7W=;JtRc54(S3)kDH#lfI8b}41IY-VcAq^6rxK&9Oe28bc44h"
    "uPF0io7=h&j}FNruObS{BQNVjj~j2po}nTpDtr0fte@>OSxQYrVd1N36v9BNA*JJA^2{WvaeMB$D}MGC<93tiiFWawq3}4YCg_<S"
    "1;v1<aZKs)emEKmAv(hl8bvQDr6)L02NY^h^<n05ZimcOXngaTH}I9z4I+xVK*hKkIFFZg@zJlwNuoSq5l$1MmNYS*NKl}b-X(f`"
    "Zt9+PD4>GA|CTn<<3-@q;wM_i6S3`F?5u|iMjW*fj)|i#(c|SJy1<Ib8RkQ&5<PLO!e)RoOZ+k=6xKndOZ0@f(vCcy?IE7uI*TZ="
    "j^aiS!4`ci6`51yX|_(XEqCXS*O+X|9{ubq;a`(^RvTET<yXBqBF>qtNF#24F-cZOI3pKKlYu;oC@eIxOZ2!XYXcvEY#5<02Z<h6"
    "b%JnSzj;ZVtZ)%Hl=Omt&D|cGMkIpkiV)o5fxzO1usWrm4*g9><Oq5J(xzX4<b0RtVG){X#>Tt3I3FPq+M~xKZEbFI+{5MH9eSYV"
    "RCh9~5#><tnI1T%2hNeM8WJvO8p0eYa46k!G;mAliQr6~)dDwg`BG$sp@6~wer{Q!CrTIl%lD7B%h|zl_w2FaLsGli5AnyrYI=rv"
    "hrMv{JME9F-?K5%F;B(5(=Fc<K4r_Haj1_sjODY9D6!`_P3gsJ!u~1WSfpR@dB8*&%Rz5+sF81%=<%9Ns$%_dg;*VhUWK#L6SdQH"
    ")xO|ww<_i&c@!3~q}={ONd78>cRCavvRj9X=8xHuN~2dhm_uF7vEbV_(G#6K4Mn_e+F;KS)K{!DX_x2;mA(n61=h1MjDm+F4nj#+"
    "kMjK%;J5rB1b%z$>X1;L1v}_rxAJfhifSu8u83B)_tyK1<vDW+s-e#T@fgKCO_GRF6ce#69Fz`FhtL|O#|67yZB8=39y58vMMPo8"
    "uuJs#Vb8+ckPb^_P$86_5MSY2uAl>D(PEBXe0hwIqYQC_JuFmdI}6|S;|WoSu7|=3(KU&lPz)+Xt>Dc2Dz=1mC?tnMMzOg`=rYao"
    "Dq*486}8c0wJYKYBGM?cw6`G_gH$vR9B_gT3LPvHJ#oF-DC-yBv2V{4JzhUJoH(MukJRl@88TY#{$wipR}qDo*4spnKN2+z$)SMU"
    "C{LdydOU)(G!zjM<4^;e8xfi!@!^U(BbvWS8nmwL8Qx6Kt2AvyVNdKX(c@2SlR0Nx^Sv&hnC{S)#pX~*mxDYM4OM#L9N8Kz|NP8I"
    "Y~wapu(mDwD5CwT6csKbRtkv$MGpLkJ(L7(zGaF9rf&pet*t7dLZsl?PsV@O^s$gZTSlxmQH1v)F^6gs<URFy!a^_B9z9XWr=d|X"
    "HFa`^C<b+G^D-eimwMqA)*7!J+lCTuf*La^mNpjAEJ%ELSwt~!YU3WB%HgZ_8V`wwL!0Gld7GU7UM!Z^!{y)32&@Jtd#s#p99v{n"
    "m&RQ^8{stoWL&$R5*A6`$u&h$QCsbDLf<C(?aFOdgjp?re!$%~)@R<Mpi1!NAkh<hUeEqHlUSW)fdlTO5MN}w_Z(`8BlLBmC*J;L"
    "L`jSj?DO@`k-&{>#x9iGcM%;72Eo)I<&l7X6kV`hPA>6^n?71Y<;+ilhgs+<e7FM@)|EKtHqjG#OaX=W7_V}Bj(HTMiVyNckM|fK"
    "*xZ<8!>r5$>ivv~#Y!mb3DYHd;!gCZ>2OS>c2?m|JRB4LmsoGxp=O_%1iB`mW{i2KQWRl_j2Quk3&N(Ihwj1eKQH&+GBd0V1uOsF"
    "p&U?`3#ulxDI^XEcbfI0uZSqdUK%C|XG(haoS~q~e{zJ&L{H4EG1MP3rbnFdL9#fJFxRF@^hEWBz=7k%@0lE~Exkrnh$%hXJ-Fx+"
    "O5SB39_wi8*JY6C_jVB5uXoW_n<#uIlyx7=HHfIQgxx<NRDCJ6+ne+3K-O+@MigCEzo)^!;(ZT98g$tP7V=PQa8w^f^lV8ZuAbif"
    "{zlB!8Vo9yY;jy>Wx_HYsQgw;Ti2IndWmhtdJ_eYn0L3a^OwwQvp!a`_Mn0)%_a)JQ@Wyuy`oyE6?NK6mUNF4A+FM%cjtw2!I;@u"
    "u>fbvo*<GRgl#qcwry@<!86hmL{c;4`<Iw7;^dMNivl@3!_SU2n+?B-yyHBo+(h9k+gl^4Ve;;V*-`l|EE9xTG-*ez4`1V+Xs=U+"
    "aXG6?*dZT(5$!bdJfaBBw1KPFM_4pbkDhSU+PV{+ZKTae6;W85ktWd-hG-pSMzu?|QeE$7cy6h@ZmNL7U#!wrRKIKfd%n-S0(3vj"
    "iN?!Ld9WQjCk^avL^0VtVXQHg-P1)BW~uJc6ERDLp{U|=WgAggCdeSs6Qy;+C`VIbZuuahm{#Pr_XulPo8@I5QD9d|j~Z;E;4_jB"
    "ZjHEgEGwV*eomdl++Mo@b^3L?cgCUeE}|rpQT%a?KChlr-zyJ~QZO^7M<F>HnZ0!8cp9J&&<bqFuSIu+<5mPN9XY~XkDgGLjP1BX"
    "K?+*ir8CDv9Gh5M?87tP9`=%X$Sd$UC8h1o@^wF$<booiu(1Cu(G%|DMp01Eg6K#^q9?4`rJ>*_x!*|kMO-$Vo_dG+Yr!;K$s!6W"
    "v(^=fo_Kxe{&_21RT2G7|6S<`o4Iit4J!&e2iLUgc-Q#0OU&v7)Zd>I(ZyXEQH+f=pw5_Luw~#mAnv?IS|@tE4R~YwM+Dc_TS;7M"
    "ZK4OxX`!NC>2bkmC(hT}hca-BL{CW3PEm3r6LZsbIbb@1IxWS^-lO62bO*nVb1l3aP(&wN!DbP=dNx8852+`dC*X@yiQolL7GtBR"
    "(KTKm(cUQv-0Jm{@9NQmy~hRBZKCiQ7Fi#=J*Ob=u>xN&4T$n6DoER7(>`(QwR|-}^3igwePO60+!ycp*=}H=RcNzK6#R`vk@v8^"
    "Mi#JJiXz)Y5wG>keiLruB<Z3}m<jwk^Ab$IjtMi9>=i|wtzKPW*)C<GC-|VFToQVt<a$&QwOxkiAveU)!`&zR-D;yyx>;qr;&S;J"
    "jUtoU9fK~SwtrE~+);X5+pNOe;1EY2>rxsDKT~DU1CK7nRRrl6O`<2_Pl|v7qg=8?PuQRW>Y6BUoj1lexy_NVNe8Lh1R+>$n+M8m"
    "DTB#W>4~e#|LJ(=_iP8r-t|4QT7!HWLY=tODy#HR+4d~a6B$*VqKK+8B71W~&54dlSrx`&?xS2g!yoS;H&I>XMV2Lcyh=<FM$z<D"
    "r1wPA-hvQsA_K19y<`$wvWSApDKxf!sHCmBjws@EXJHpP6xK^kxeZnRsbWUw@nkh3{2Hy=mL2MF%#^QhBTCE{RP?X<@)Qde)Gb5l"
    "@;-`aFOo(SF@C)FSTeZGuu1gD+)U7Udc1?B>PsHQ>DY2Q0ym~(JUq{D-QpH-zRxv&DsI8W<@)|JlLJ!r;Y>}%EX$i)*cYdSr=|{R"
    "Xc12K05_vkgmc9eLj=NYICiM(TR`y)4w<jM&9swq!i5yev_?2rWibRS_29tw-rCr!>n}vj`Isva;W)6oHP!WmsWlO!0ef(w(?lIo"
    "wj=!grECwvPpZdiPFT6+?$bFF-c_GCnHvhJ-I2v}H|Oltc3$Soi!<i-&m#&d>ecn=30r8G+n=A2{DNF<bjO@Ox-<ztN3w)`GecWV"
    "r_nLhNScUZ$|40697kQn22~z~d{I`1FFKy!>BfcKP=Z39HbpT=^hD*%Fp7KM&31^myD~)7DE9gnl62`$L=S~q34&yhIudw@c$to^"
    "0I3>QF@syNa(+*7tVPm#?CR+iBxGU^cprt&HtS)XQh}69ikaGd6k+gb6ZYM{U@3J%4q%T<Oj#b`Ro?sFvwb{v-ScYD#{yjHeJPQ}"
    "9A^0AGx5C2%ZS2K7u!TnTugTGiFCp`80$O=syNYxQJB!>cxKU{Wiy`439F8~n1k>~TZA-&L{G?&z_G*6Ody=17Pxsw_M0a7953W0"
    "`++K%KIj9nDlzpf2vN-}0k<S0Xk7R4Vm154<Zaavg(ZD7i5}0JHeKk3r~sTrJxx&Ct%6y|Vpe)cN39b*ksoKXVtNu~7C)&d-@j?~"
    "|6MMx&sNVTL}9l<5r0H%k{3gw#Id?U6br9{kBVvgK&WPHmp&G+G@I3lu~fr(Kglj(q0pT=(Gw}#VTK>53Mzpca8PuU?hZj=Ay0Xt"
    "$E#hbgZ^X)nd92f73*Y3)Ke`(PSDA7BCW3o0p2HXmnTdgSiPs*JNo@&ReU9oQumvqB*IFaK(^msPmUfF$Ym(CdII$+mffZQelq1Q"
    "2z|~=8{bo=?`;uLkOM^no|T@^=mv&b%!tzWSwca9H%*@C@!COpzD~}UPv_9Z7iJ~&cwm_7S`LMT6c&lkR3Vf>6;OXNAz_7m5mfXe"
    "4~-p_9_Mprb6dUo$?WPdmUOy=t4`&Eh(c|xRe01Z3fc*_rpWJm`YO@mns6Duh3YhIGV`2EThq7j$vIb|IkPq5Dj#NbKrL{s+do3{"
    "J`j3`mf0-`F-iYv(;ZGzQcv7;2UL?RzhlbPXXrFWYr2C!66NC7h>qzKrVpLdcj|!px;py49)D&=%nduHY>fJKL*hCcgqp)sNR1Kt"
    "JdHwJXZl{4z9n`=^oDp8R`;n&^h6D!FgHBvAPeTK>Dc`vQFlvCNz*Y@I8LsoBGD5OU!|dlPA*w(C)c4qGg&`HL}6Ch&gf@MPNn)O"
    "JPMKzsy-<_(Gj2uC?ccH5?iKYJRU&Q!a);Jm>St8dfWvZcIoPP4~e%l>$jsn0Tu5o(c_r~O+;NWDBA->gTFFFi8~Y+ho9w%p2*0s"
    "QJ~HaRT>3X8zd^Du$@NSUrkrEO++z@v7Ut^{0{QpRTv5{e9;Eu!0Ak+91_E((UMA!#09AdQRxY9Z>uP%<6+@m>V?sNV2b_fW6Gnj"
    "{h3B#tcaPR;Cva0=~c<*QB0Orr6^**72%xz{W(=`#U2!Y-&>Er;Ocj-%B?hpI7OZzxjJQ(p12osMXmn$Mci~<7E#1r)p#w3!i$bZ"
    "%j(Bp(ie#^%IOS$;a1!x>T({18Rd#ZkL$o%C)1&(j2oyNL=+~y(<n^+t5Q)!5ow8Tt#uAm5n#(?KielldSu5Miio?&gAu@^Fx@Oq"
    "^!PolH7$KS)$he@`Q|w!E#urG3eWk{Lfjg`CFQmM_hUxUEOcE2bDD(PrP1T}MH^l#9)(5h6p0?MyAr<zubNVY{7N^6XZy^qv$594"
    "=L{d3h{7^$(<n^jiT~55W5f;ZEiF}|CklW0KV9r_IoGPIU+f?qNd37h5<Tv?$>J!7Oul5RC_<97p^TnKK`xc5Nc4ox5JtgU0T#gu"
    "bm1dH@#1^xC~>GMmDL-@`Y}ebdJBEGDm{|btM#&!9*^M<Ys$6u8*~u`^}MT#L{I4IVU%~24JV**P1SKvt6*LDpi{yqtvg{T!Eb~<"
    "Qyc2*oQO<NE0ae-X7)T!^hCufn;YJU$LABZhPrsmShSSqL#pyp{4U5nA#dI~(GwlpD?=R(iH_}69#Mo8vXi@s(x`^zkD>hc$@vyD"
    "coBx4?h~7;ZX=56GvX&ayCjP0i-7VQc=ih~c<9Z=m7zi_YAmU_Q54h!EenqYM-La`u4D61hk`4<dZnc{6x>7EtIEa)$uxmX3O#x_"
    "SJ6zef+7m7mxI9V<H_%9`7Yc*op*V{;*p<OST899_*fWNuC9>TFT%VgiGf8#A&G>h?kYWQ`csG3^#re%D{8zd5+3FKP}{3wmYPGS"
    "5TvrDzBHAd@VWSHz=T+f9Y!s{5+jYdoAV~o6R9O(ly7q=BT_S$m7dV6Yei9ARO&D{Jf^*hx`#($0-;Itcs&-aPH=rhZ0s)Bg|4Si"
    ")<zdXFO(jy#IA?#`U{dJ?diKj4+N=NNQ}}GFOepoPMK2Mx|&~>yK`I&wpzu=p>S=@U5=`MdK6UaHBX~3z6Rq1(MwwLeKJFRg1Q%#"
    "YRy)9!a5N+fcsL*V7>Gx?8LQ+p6D;o1=MGvo?#Kz=&!}{e9n~J4nVl8qdbAjI--#J41+<B9*O&^(ySO^WuxFm0I&OH0rizJi-obM"
    "(gA^QxSr_?xd+tll?F=_?w+FEz(UQ2vLd3ON>i1I;?;P_tXD)4odm1Q4v2J207OKU)rp>nwhbJZoMRmp+C)zXA`_BQ6BswY*!B8F"
    "i+pZ3zZ7+%Cj@x-BE~7%m3DFogHj#>mOKh7Oq6Gd9)HwV#y9zQ;*u@w2jPyNz8rTGQCNOZ8ig?FH{nlU0b6|tC_N$T0t&uleNb7Z"
    "e<I>zog~rI?NA>Mkn&mPs8V_&p0+jA#ST$+b<jl=wx(sGC+;J!3jR3YS_P?c@?%W2f~rH@`;X61ny|>LR_XEAw0{m{5rsVmdi3}+"
    "N|ic?`Y^)n50?7<b3z0$I<-?@?j8m8P1gJxr6<Ci{QmhlMINnQ;p`GUZe~~c_LFEPA_?PuZ?B)smQN?k6Q~@eX1=eV4VTw@*wHQ%"
    "Jt3?bMRD(3|0jn+wy0NKnnX_|OcfqQ`2GC?RV>Ok*wQaL`aRz#EZAOIQWRu3^*$O$Pi!7B${7l`{QHQGJffh=iglIf3AHE8jqw-c"
    "wttRrzrU}Tlo{%nNg2q)3{TFP*J~9~kTA&yi5~Y6w_$E@td5ko&C7_wBtw<xamnDHLJox}nO>6g=y4Cee;BS`Ou2qQ-d5mHlp0g{"
    "=YvDx%C@(lb`b?xT)lP9=!wUje$jW%7V4cuf`XHIeTrNjQBaDUkAE<F{M;!Y{^wlmf%q{O2IhSr#`EG9gkZa0+`T=b5lNZl-gGah"
    "lkFwPt57||=!q+-G}Ol%B7npP(kP1Sz}{M>tzxBaHXNkqRe~mA5tYCPIT$@Lip>xbN<|RkdrZR!*-i<CZNECv<HElRqkMl$l&w~U"
    "&7)*}k?ToN?IsE@Tdk^*VrP@(0aUg+vy&w#Xojl3Dm`9TB-2q22+m7JxpMwsxqC&ZI(D)SL|Z1j-a6JV!d@yiOux_Hyj(tIf?o8>"
    "_9$%Mc8MO3XDGwmaJ9TJYqK0%rU{*f#QU3ckMxxfv<S0d@fWTtSBAP-`=Hs?Xv!3L$>T3z)m@rIkB8N%WP9^+{p?t#@p=pt%pcg@"
    "8d0GCqUs__Vr+ndDuN39Pbl1;ocFMAs6<O^@L|}CkrZosb>{mM;r^P$rRASY+)iQcLdCA0jqrlZg3X$Q9Uc*>VMTai8}=)AHhbLW"
    "?)}1=D;d_k0U7nRYSKzk)y%w)tl7XKeg~~B6HqhiOSNr>VJA<BzSV_Uk_{{MsTdAdJuXp=KML~{L@eM*OedWRD)zfKof^)!RRpb7"
    "vG|Bx+PA_|AW5x`kM2H-D15CWUJ(iAmHA8+g(cT?i5|9TYr=~|5v5t9-tJJJ7-=)G8A@FapxAY0x7C#|n&iIgMhu}>^X>PD!<t0B"
    "qGXFb2^|VAeVK))u1BHqlTKS}yM)5aDrOe0X+S9OvQG3w+_nFx{UbuPmP=4kQe#|hlc!&{FP3!5=pt(MY=S}BTM(kNK%Rg=3j^N_"
    "^fm-(Mxd8tgb;-eiUdSLuj}4GxNpu^^<4kkYbvP8%#|L+6tAld#S}KtwnvJR1|=_EBMBWEYi%f~{#%vk2`^Y?sH-_+Kr12&YwlJi"
    "di?E^8Q-W>#H`IC3QLKq5<OwSHx8`ecZ4tITt*c1K5fFcAUC_bOp8R18<WExAY5Qgm+QG34;fcZrfJvf@#Obn!IUqkA_@xKEYc{D"
    "zg5qg(&Mpkx|-w3^64e}HqWyj7Iu7S8%jlCj*mLgGeNl?+axTG3M=JM)R~f17zFIAi98#T>#S^UL6GaLxDA0lH5#&Iz4>5cQK71="
    "L!CfJxX9W>kBjljHay`WZLCUzqKIg1RV*E9JR(XGb>Y@fAQ0H;$0~0@h_Uhr#0Kio6Tt(vxJ1lb*JC?VASIqhq6KXzO5;$Hj*WB!"
    "S6jEz6P97+-XT##zR7}gIwax@C4@lva7akA*5a1e<0G)Enn0?-EeK(|t_*m6xtxxeOCbQ^7z~f9BZ@X6>EpMD-Nu=$D06KbAgJ$O"
    "<l?&+KAu!nwr!%H@8DnO`*{r#cCoWOJwn2PeDr1)fs*Y$Ar_*l)1cz+x!73`7ZNJ({`=jWDW_JY-}&=$`Ezgi>1w@;7rq{JCdd3Q"
    "TrI?0GkLOl25K6*Sm|3<!|C?L>e8H7<LPpDwETP^He{mIb}(n@j~p&myT|5Az?Yy%%O_QvK3$Q&V66(|7Z#5t{WUSxWqgFYfh44@"
    "wQpRGhGIKHlJqM(Zp-rtL?75F^n^4n3?;_@Jt7t*NRs9MB3x9N-O)$Ozix;`&N6)3jL7CL@;0I%#lEN#J)UD283<&4dHO8T<LR7v"
    "*bH;L5Pei%nO@Hlwpv7#Zdbe;vUc3-W1-tKuObSfFS|sK8-KzslKwR(`;Qgp$wLf)5HqD6O-nh#TSR$1DvKzloQp9{@_iuNMU&|9"
    "EP!w`iZKcajI@{j(aJscVMWLrt^@ELQwgvMD5m+TmwP6NC{z)7cy!5x=7zCw9lpvUL)OC?{-)N_bAmd=n%7r#q9@AK=oeisXJaHu"
    "ywJD~r6*34jY9P3X@eJU40T@i-ZVXZpNS4rofSt~kLT!xF4^dnLEwrmKCMQ#ob-=F3?2S4l0^t6PTNEezpc!7?@;gdw?|XdT^2rn"
    "H91>;Vk(Q)0r-ASxXZJ^gb!~Y6ZPV%4xf+o<q`Ti(G#(|ew24Fsmjb2T=(v!@1}}Z*sCK7yBfMgPpnHA1wJ@p8Pg|*LwzJ1l&$6h"
    "ygMgMppx-jL=<8Q)(U$@4>_TlL{Icet_(#vhSY50QSL4#g3tt8BrNolNHfIhgO!OM_eg3$!n<>*!l$EeyF^boh6aYhea)4nysiJ("
    "gB(M0iTKr-42e1hg*9%wi;|wvug6GrCSNABvLAt4tV-sx2I@Q1UpIsh8yE`omudeyqsMJxbr@xQKrC5SMHCV@VliM!PegEqFM@SB"
    "AMF#qXugL;17><zC_T|-&qi4v9uV<+#UP@fdJB1v9y%IDq9?j#DQW>0R51h2gy>7?FUlsMPO<%5C3?aNZ78ZFro}-ylsnhEXG}I$"
    "-3MX`S@|sp5iJwOx*ju&tA}WTWZU`0?GinqX&3{Ef*7^c*b&qi2;HyKGBLeZvO3P~52j;vT}KoX^kPSe>AV?&yRZg8vPS9wA-n%H"
    "jcq(C%PcROh=NL}*%i4!v(mz@rb<AR8VG&3vwpRB{Ka9$hr`zlufooBsN?VATsV14)poOZlEc?f_?*}uibPN3J9s(lE+8Pu*Q?M*"
    "PpQzRy*LzH(#q>RgNTCM>&AftaS0voAW?Jjh$wm}s98Xl=!rX}Hq^;J)5suj0FJ})Yh*LzI(Vw4<WNK#tU=XA6k+POXaPknMr3AL"
    "!fL^R#}2PN601c2<`B|?8f#>1D0j)eAPSdN8lj}v*#Q&rXq`6$)@{@S!huo@Hn5l*WphMgr!~DVz23u1{`%9Mu&ZZJAk&9b+h`MN"
    "xIlW-`?^m()b13l)KPYKPy}bvF17xNcx-Kv&J?zSy?HVv3T2*MT7Bm0(hTMQGZoCt$>mXuiL8w%OhXQ*{v8qPQiQvJ$SijEP8H7G"
    "6pZBT5<S7Uz=7$Q;aePQjJ=q`e!wG<M41d{88)%{fPdQwRBfNKu`hC}4)e%rA`06-b)qNEh3-1JK$)9Ycim^IJ%qNWcPPB5rhg`Q"
    ")cZX_ZGR?&LMuuSm#N7#w&DFAV%za<=qk|@#c&!!;RbC%b%p};YTtTkkm!k=Fa4rRA_qZsLSrbdyiaB*xP++>59=ZdiMh%HJ+A5b"
    "FKQ!-$y^v1>fJum2DgYPsDfD$zKCh)W+hWRig`GPxt&mt`YNKZH(;6Q@m*I0ZcmxLTG*~5&V`(&+)%isv<x9<?=Pvy)uOSzhc^uo"
    "gOVB_K8(cD4oFCI`6)eK8&g;6_?#=(tUUK9s9dwItkM%VOJS%tOi7&5#=^_>NZBj3KX??9YiY6EN>6l-Fup-DzYf~wG0|b%#|7!!"
    "u9g>46M#{l3<wL!Zjk4NSA>4gq-v#<nz;@9*9U-EWkG!s`FzKQ^AJkh^WHC@@zTrNRo4IY9@C0IG>!e<5bFo0Cr+y{z0(~K<=xZ)"
    "btjeJ!H??94=62r#<vdpzuvPk+`G(;QYCtV;kHtDA0v-_k$)fy>U6esZk_{GqKB7N!*2xjcV-Kf;fv-d%I#Q9+;FJ7-P0cALv9@b"
    "1oeJzJ0Ef@FmCkV+{A&bd>AedHcc-7dcXMUvNrO3v^qK^j#5z=>Q2qNN4Tf<>ff`s8!onc`QYh`L{F@dq3(*l$97Sv+&kJ(z3x9p"
    "efryFtM8|;<LN%aXXR0Tb-vE-hFCwc6SR({L)|T|{@_jsMRy}=Bbe>}@5;hn?W5p%>a#Imzpwsyj?Y$~w~Adodvf==@z_c6vGECe"
    "wIIgTb?;%f?_}{{=Lt2Q{+@3_dL~~#O3|Zt8}g1?``Fj@R^PH_o;|^NJCJO%v@Wa3xvzAA^QX5i??2x);6J$A1v|KfeX&Pii{7}~"
    "Zg!#fzAd9aIp6TpJ-Cidl~B`rs!2S0zRC?OGNM*hHI#OVB}S|^u-J)iHc{{@Xc@7H1;*-~CS1P7^E>;6@9L__BWlC#a`z1SQL;qu"
    "l;Jx@gNMfQnoqZZh4i1QH=<Sy19nK=C2p)<{ro)}%ZI>h85D^v_a^8)`k9+pXu?(3L(P8w<0mm<f3{l{cnO~BF^4%m{_Bc9cKh<>"
    "<z0IB%WiM?BkLa4e(MA$v_5}YuYXCL>TKvEh2RsRTD@Z3Jl!rm-dl~IGn=RA{lYyNaF5+G`iN8PeR-FU&b&A7e~i{o&sHCHkiA!_"
    "Lgj&ytvUan%!KoZm3xi3QU`4hI~m=rSokP5eeCLRAt{G<(mWrXcKT#@LPb-WUE*-He@6J-Iuegy^WG9W9cKA$&TOq7_ImD~C(NAF"
    "#$J!VINg$9m$yX+?A+ULxs9FsfOGqW$<gxD&9;lizVvS9>;t3xcWF19^-$lxEI-Lb6MC&)Ew2yse=dKx+vkk=*$V$zNP!955N+8V"
    "x;I`Dy2s}Amxmalg$M72{3rXbKW5@a{qP`9t8ixS`HAIIsRZEeNlEU1c5Hum__s9YnES2&BrPa@JaKa0{g40hd+~C$d;DJ?o^1Z`"
    "0A3FOXIixn&(v$;d-_{jf2hgJhkxi|=p-jFmxmW|{pzRq&bR+W_V7<29O*Lku*pvV&vc>JOIYb)lS38{%?C&W%G+=z?pT^1y$5U*"
    "5lf7w=FJ=31{N{E41$cg8%h0`Nm3sW--h_3JPXD11a;f5`|#7DOZ4C<WttnMWT`h;RV4KJRR?|0qc#F|9<&nqpbyi<uw@cdkp_a4"
    ";-*gY)SFUfcnb^Iy?XS-GPQ;pqZ`lLG8;p|R>?f;qmBq$W@jj$=rdW)xBC;aCfM^RJ6UUq*T27=Z8*B`Kekf5zfJV`t6E<Y-_Gv3"
    "tRECCZLn>76f`$m*)!aeAlz2F%eR?ip>5saouz=divT%yQpQA;zWEMeN34Pfa;Q7Otq-Ey9#GX}zAw(nt=|&&jM5WVQf;W|87Ath"
    "L{He-{V3nx5_}U>W2o6@#ul!qtL4QWa~ZXU!q-R)G5TFscZ)kdcoy6)trH6JZ}>3h4SJcX({;8P3_Kg#1Sc5M(I^?~ew6&n@ILd#"
    "y?fFJ#R%kfP}PGU*r&%830)xfO2$7>wu!FY>~8De2X8}3O=}|x^S(BTp19ZiC_kRKw=5x@D%FQa8>wawTbf&?znk&=nEz0f9FKw&"
    "Y}3+5xWvc@K?XY1Y{EGF1L{uImdE(!LoFPNJ61d@i_Z;*8Zy30^+GR3gicjikvT!VI7K|17A~Rm_$XE2!vwf@DhqjY^peO$oN*mx"
    "MrxH_h%N3(rhHT{@~EFX?&+j)6X=cLX4-9HiARTOR*L;P_g0+moYArD{epj-GT1C(;qNtLkD~N#e&L&3J!I^W3J66Hf?b`Vf@VTp"
    "?BI;8eN#KbdhtknV3ua<bWuX>=`5nwuzNd@Snez>@)n91vF>9bWmxXCypQq;890A>-}vTGa`NEWYJC^OYF`&bb<YQzC_-rWMx4J~"
    "AAV-AO~U@zp+rjFW<Bf>w<-v>D>ty5El74nn)&MK4HS$c<5qnX9yB2~^|HQ&oqc9@RNKem0^bKR^uAP@1wH3%`CWKQ>n{wCAQw~7"
    "8+0_mwJHCx>AsMJE&To7S(${0y_>N0*d14<BhPQAZUc*OsmRk2kfNdQ8IM-pn=R`Q>q1y!fO9gu>kSPUBJ#X<YK|_cCrMdkeXJCK"
    "hrcn;yA3R27_5rkIX&K4PmUh<T$Oc?8z-Fex$LPoR49#qto4qVhN!Tcwi)z)VY~F}sY6y*j~%hMX{GiXF2}kMiJ;g+CWNpFK|sHr"
    "ZFC*HU+oXUr^}~@<ddZIsLS88F)=qA>yi+3Vn)amg=h%=i<(4Fn1x$IJ$u5KYVC_4bEud&vP6%M;vX^`O2*0!1&0$#FmlzgD1Sl&"
    "_bzr&V?t@>6h)!#kJ5sz42979e>ZyEY#a6}5&E5_l@bX|a4({WYq4(fh+2M|FRz@k1V?T*S=@^FJuawXkWj!Cqmivf??Xb^P?|jN"
    "dcVNLU^ZDi0*Ki60;);$`0{m$Cth#-%EUES9y{kAdX28#d?T&u!ADcsqbEkm4TU@;Mc@>Pp14XX8kJi$U%BHDEnVhTCVIjW>-XOC"
    "#q!@@65?6~&hrKLIQ0pa%U9>156iyj)j8*O_l6XQ!o^w^T>Q)3OCmEPv)ZB#MVyH6u2IzXGaEcUMo*|%er|g^k~l)x*fT>R#+=Fw"
    "4zw93Hxzjy3Pa64V<)0Y^u*rISd`C*3aD@USVmNv=)qlD1jS%)2lU59J`*<lBF&9@+!b9wN!0BP;c(B21SFiNEsOFOnJv?5JS1X`"
    "d@`t_Ft#^={(#YD!xzCu^*q!Q6%?#F``D!LMek?0D@0SiJZjE-SD4|4w@k`u;KuQUaEOG%OK8GfmN<Vg#8FujR{8o1cAa&Jp7<hL"
    "DS2WOr^CjQglS@Zy}*?8_aS3yGZY?LkOiBSqM$RSYPr%A*LugIWToO*_zO|4Cx1Gmdpss3^vY0rLYZt7MJPp0I86?9F(O`wg`uD|"
    "ijRvoLvD>!nPgC&d%2--+fk@T!l4Eht|s1}?_VAa9)Iy#>JlMYV&YS-^#_-qx4$txeUs>kX@^mOD7!2ae-ip1JJ<#;5<Q`x|8uDF"
    "UX+-E-&}#=IvQ5$n@dx-Uc;iiRujfz^b>6yBq-dq-B?VxqL78NC%L0{_Z=KNtqID8f}RF#q9;zM@r`)C)!_zrs4<qju6lyf6BaW+"
    "%Klp-LOZi6>C62C#FUYTa4#pQr6~$=3)hO0TiBO#U_v9BgvEmc+q#b;bV7MGRy`~m1kxs~52a&#&1ueNDxtg{atac!(C~wz2f3QB"
    "S?7)zLh|?v;xfjQEM&sn1{ON(#UP<D160wbbrE;%hXZE!_9n@$i0V;2ESC6QB-H!Q?mvhf*!7l!_4IYc2A2Qc`+orniS)4+hGh~Z"
    "{J5J~XjgRECJNW6i>i+Wq<UBvF1$93f+txF!tLfz*V|8r5BRJTJ)!OExj2?+H-c||EC~)dC32&b+ls;?e|+qXL*1>K_LyHRt0Icg"
    "`R%*#!~w57w*hsC6w)x0rqh|9UNJm3KA`6MqD}OKdA10sV?+lt;ji?#H1>hkg4#v1y1fb1pT4UJa$1F6bugtT(v-Xuy7Iwz|1sL`"
    "p>q(mw_g$dmuwJJ%B%TCOY{4MPl)I?dOV`Lw7H2}d3MB{g-(HMyqrmN++2OfZ4MsQ-HQ@K*7yK=e96|;g<C+zgerJRt`_98t1{GZ"
    "%2>QRLyZZgMN3mJuWo$IEhhRx;;N!#LjopcFU0bQf-DB=4^?`k`j<X!lpa4LKJQXGb$`0r=o9|%F}V%FO;~DP`)h&J-t#7}F45xx"
    "R?U(Qb<Nc8@u8&BloIy?4y<*OqL?_tE}^Jsfk7~3%t)t+`UHKgMCR+dh|-DzSXf%wN8K%-{8+e1T!nZ0(mU5ZpI;nosZ^oIN+FCM"
    "?k|XL1B(UIwh1+Pa<|XeV<R@b58NsQ2EmT4^w8Pt%?%d<gTRN6H^lv=7vF5cxqyv(ljWxy=n|=vV-v*H?vH<-=!tL14235a)xi)t"
    "BTCBo87gWfF~+zJ(?rczGD*!)L{UtMgY`4KKEPv`{S4cP!Y-^X(c>4r>Oa@xyZtd9wfpH<zle~4c$&WLbIDn1q53w*%SUA)HBwQ~"
    ">q8An^OtyZtDHXF=MDu1hv=29^u%c@6h*uZs}SzuP$v^+ESsUo6C#i)ppfzfT?h_Qdfc<0*&31Zp*9rmZ7&1&en4SA{{3DjdcwBf"
    "+>3JmA9UhKV1ORsA3OMx397swC5#$PprHrh#rlIOXr1SkMos*9BF;PLY*vXLkIS{WJt3mIWvs?fOyX@=f+x6tJZpP1#8vAq=scPi"
    "2A#D$(G$-`+0WwAh3l{T60NPF{`M8KEH#Oq@WOY7`uCTR7heBe=?S?J=EjtjXbKz4X+HREr5)82g}J}GL=Po;r&%#KuW`WbPo}zF"
    "9Z{SmzcsC_kA(`(_*>XeTg_js-9AQ-{C?J(6`>mxijuwukd$i^J^t3nZ0F$KVLz7bAH3?9A4|VT9EDUykH?k~%b+Sl;cueGt~OB;"
    "kPMwB&5g*lX`+POM6LhrwKT&-FVOHKhYKdkx-}G>xGiBtc1#4dUC4xVHls(Pva{ar<6E(^#lovYcr%4=#T#ucf*R!WDxxrhd>Vy0"
    "_@$wcus6A&i$srG|Ljt`q3Yrfy4Fx9`?%9w1}g`BAY?o-u^AwQ|1nJRBNIYj7~92aO`vQ`aD}Q&V%%_XQ>M4vK$=^d_(1BS8I9`V"
    "J#r(BK#8qx+!MVQbgEYQEeN6a)(HrC_5-)CkEr0Etk?i@(Ky;jJi>VusJ#n^c1z@s0wF~xzXict7F6XeAQd>#CW+UF6JL6Jfv}@="
    "8-ic81Cx7F&XKLiTGbm^$c|?x@fY!0kz?gq>Z|B7`c?Z+p*ln1?&HuWP*9&3O;vZAL;YZ^yIH}a{8%<aIR%6pt~S)i8^{f(@>%JL"
    "MqB<*&ps@_4H=o~Wzn-^$UD$kfV9yQcSm8UpF@1pW})zr1Kw>#`{?3&)bNOC4JXgiN>OkLb~Rad5ykY*vKbQTGorsVhJt&Zc<=cj"
    "qA>ANC3>RhfqfAwZ}sgkB!sOGA+v8GQt3qr@tbydjOHv?J$gb>YzzgPgT(Nn0(N-JrE*j@7UgEj8s)jKDMVgX_GTGQSI55C&J;6@"
    "Gy_9jV7(S|<;Ii<(P_e~ZFq*5YrKHX6Fu>sQVx72%o=4dB{@wS3CIlD!A4K)ht^OZnd*XrFt<=@g9vRkS@e}C(~()nJcoj$gnU<L"
    "^vv5|TbQnfi`Czs6IIRi)W6sR8)?e))N1--Z@K%Oxt<zDtzS%;H?L>Ki&MgbFbG<KLtQW#b3RT(+A}aI>bd^Ompj9Bi8j&WS3n*{"
    "0fc!TJWxhY@Xb(MD4qA-3X01tHf~G&KXQly2Z(%u$|73?h3}s%^5F~aS@zt^6-8KeLiUpc&@Pyw&3bHi<wP^Nv{gj?|E#_3avM35"
    "C44J;39Rp`zw;3@b62uWdudA!Thn5jvPduWSZ>)Jax^W|UV2B4xtRTDQupvyB7rKPiY%Se??y~aJT2!TP(UJ)U&zExdeqVrUsPEX"
    "Q^YS$>^cyBDp~TxqE<7i&yoocmn{}rjo8tDVmQ#QA)f9VxoV;u%B8{z>i1K|8Y&$M>lBkzEj<x;wyTHd8<-2%%?*(fnRDjX^oZ3d"
    "dGAR}Pwc7t7V5=fgMxboMy^t;pm4P<vUxr=3T<ZV)&XzNVIuYBi%wqRE_xF_$P^_BV+1N!)b7huCXdU^a5~;D2o*8W)sxiFJECi%"
    "+WQ8@+%>79a1J!Z=gk^UpF$a%Wiz*@T;04}Q4^{SwKf<xsE??|o2LN;AIt6(R)k*$%369{LaJ1$QB<|Y%%T1Q_3FH($8W&I?$K^B"
    "BOEw!i^BBDxTPofr?4nI^eMWHqVA;G8WF^7QCJYuqbK&%ti$i8P-dg7K-tpcZ<k6tis+xu&ZLP0@O&v!U$>(0*ZS&7RuuF_RZCCo"
    "sa*%+<+%7ok_Kg3!yGaBHlqg1W$e4+W<D0vC9)O;6of3|c1^^;^!3~B`e^&&1M^C~YJY)x;*r_PP8JKc$QD%MqaLP@y_F;~!_x+J"
    "zqr|6FNT`NXSTt(&|_MkwbYcJxT)R#!Zo8Jmxpgs+?lAo-JLaIYsk78)Eil9qFK6fyFp>PV&2l@5<tC1vqwbrr__yQP*}ck+0qj+"
    "I5*1dim{t2ivl}r>e*3xLhp571UtP=V??*ww{z@7q%A$6UF#Q3i0tl0_n1wHT>8uf$7d5f2x55E-14(4A^_*!2ncFTh3(u}RKX&>"
    "1!~j}rk0v|W@aA<XK&f8hM+L3A#3Rg+cQ>_X!7bRN2H2sFN%VsP}S1o8mWe6W*@1XRV^~SJ0Ih|N136X!Sl_p)tDJ8Rutj6O<b7f"
    "e8W|=P_68IgRZ&yvXq|4J2j}cQ-l+Q-c&xZ^!O;|y?-B7-&0`TsfnSOi{R}iqIXH@V$B8xsnA8z(i4fb6^n{o@dQCp1vHA(qVO_+"
    "rMs-(e&UKKrYVbxGH<LmE5>}wED9@trjJT2J#l5*o#Gz47Ve91wr@oG+fPJaUFp9WIn)L*Ep5V#(i2}~#LL?i7u8j@szyzj*4vtL"
    "Nuh)v%$i?3MNh72UvBA%Q3{I!Gcin)EK5&>LM#f;<T0jG)}V-Fyfkl7ka}6P^h9!(Ljg|C*wuct^h7B|hr*xph>Ip`P}rWvEj=#f"
    "G~eLjHPl7D$t1ZTx)MiC;Jb&~E!OpHp{vuC-Kc-${?&8h*xCbihIT(x!KL)LNU@uB#=X`rbBmfWOdGkeI7`Z*)+fvil|9bLbTXrU"
    "%!xQf+`Lqp6YnKsS0hVM_-eQp&Gj{e+m&(iDr&wY>`Ga~(xU$S#Jo_h>_z!IQx{Z~mKufEWJsDdBqFEAr=j2Vk$Xj}SC95hgM1o!"
    "OHZ^XHlr+#1T~p4cbs92#caF$LA+cr1r`*=xq@RCQunY><1NjKR21L}&a0@UUmX2fpAI=Z8x2$Gk@@J6S9;<>x<yI!8R_a?*jeE@"
    "v?h;H*9z*bV=@x6mY#4Q<rc-%Y%w0lkpnXFL6wRgN}dscS8C;M|N2Mpbp6U@8`gLCJLcJ@-GvQteT(qa9lzr`@2H!4aYvK_7SUu-"
    "rr9DUnyQu_|02`DN{;y(#;v61w?-|F7}iqM2i(e*VgjnM*Qol!noV|-CFZ(GS`_hJu|<9T#_VsZsNIVn)T^RcV+1vDz9d?Wmr;X4"
    "I+I$aReFSxvUXOCz$q;19mPm?o49PB#Igi_c%!D4#qtsE8;_d{aVd5m^Ie7|mSZBHEp`WFIfbgt#7;+5dcuWLDvG>NEDG1y%}(i>"
    "&k6fQ>h_lwg;!^lHO~}<clVB(jM;yj$g4m+dsAJY@9&V>xp7nB<ozA-fT(hjg&KvgL-W44MooV*V<i@aTV#dfrT0I%959s?S6r5e"
    "RsgF}RAoF{y`)CL?+v3Si?v4Kv8}}IGF8o6lwq@9e=LYdvDg$@gTk^k(w3gEG0mD^lU?t%yukI5tU3Nsk*$R*4&gBrqcN{*3k#Xd"
    "AbO3?C_N#WV~YY_okva1r_vLTkL+siF267tar#A~V>7YQszG6~(W0d%<bxfBav<CC6xU<2WBbUWE{`xhCvEA8O5<*B?s*-ijy9-I"
    "Ow?PsZoC`MnfK;ZgThWkGYV7uR&!-*6kPn)I5aF5?PiaNj_Ml5Qq*RGw}v#>yunJ3xfOLM7Csj58E4*ij2bMWrQ5t#rLPT;-=L~)"
    "aT0e?gmbA~8LnGLJ?^M%vDAGh_DJeufs9Qz))MO<S5+-NVI4H1FnON2`<D0M>J@TwvQdkYUR{?>_cYNr##e+m8g+k4u8#{TL4T;W"
    "vwhU5koup#j=9<<^`Ln>C=^MQm&Hj7nV1^XNDuK*)uO1X*O?2QcvwgnHX>JbdkErvn${OZYNzB`gQ6>ncwC29*w((B7Ikjkcf*B<"
    "O*MmdWuU!_S|<5B4SnP@v+gfI4UAfz;VRO|h<OK#F+ky?faW9K_Tl1s)bjKFY(DHWHw<RK<$k)x<GhJeqH2^J?Z;HMNflrb7rK*0"
    "0(tTr3@)cuhxbr~&n;`PVr874v5(@@yq&YWAe(;1=A3m=#4Y2ENVZ5z;&wwdv4?p6Uz9BtIP!58xAbHet)%K=3C7DK9}8%_DzQ(A"
    "*MF7M5LO>?|5Dskv0MG5%G5-f##W=AP6_Q=eK-cC9l)8)^A^h$rVurG)M8&u?qA;BKYhteJ8j`qyfSrueh&-v3Q4>P&pzy?cg%=s"
    "2MZ<YtIJwZ4_4hwU3^OEk>8KKSrG>(wkWg(XJzTB<`lWxqwkNP8$7dXwHu>hk*IM+8Wa{+En0fwVA>VKTY#ArNE;NSszr9iL|otg"
    "q#7y4Rnft+S4I@2?JwY{(wj3`EHRBM4|{jdTpZQ{QY>fzWl;<H8y1i(QP%tdkvlC{dFcbG#<EFSb+F7C3?_^*VctUO+k}~Fly|X^"
    "SRPdYis@i$lQ$Gwn|rG-L+Y{2u<+?2xm0;Wn0AoNzE?h$uEiwV;Z0cjxP2jHLg8UeQxB$ll*h5A`2xcRE!LKoL>xZeiKdEDn)<{o"
    "pGy_5zvwoyskh6!$t|S!7T#x?+8xZHE;?AkE-1W(VoQ5@3`un9@=+!kW7r6doq{3sCY_!*GDRz;Icq|&aR*DUkH5BXSKla{^TSr5"
    "zdqOF?eUGY=>b?S@osrZ<R110m`55dJzf|jYPVbJm@$l<rtJdWPv_g;u87;Jr~>TQG1NvRu_!zP%9MsM+Rp79$z6<^VmP;RB3#lu"
    "*{)GkEk`vTZ<mBAmphxtps@DPRZCAK#u$#eWs8QT7WIm8&a1s<+Nxr`AWQuzquSvmHChx@QbU8n>j_y7XtWn)`b1x%4I}i$?s`Jy"
    "@I-FH1QRw-X4cP%ER-g`{C&zj>d|Q3_fOj;Su(wFiJ%@9dVQ&^r6}U&O)Tn$aiM1;5A}_CQW`fv;?vT0lGsv2Ej{sg!ED)&C0Fo4"
    "gL*%f#4E_eCF9koG4t3&B~=e4na1z26PGwX`2h)4Bf2X~4;#^Dl&C>HEV>gXf_^Y>B_j8L_XksBZDe0_+&`HU{WxSOhmv-Oxb`LA"
    "r78zzGI;dFDNYUQ8<CA5sH{QpGAiw0p@V7UhD9ODp^=1^{@wEa)y<G{SXc>f=|Nq$uy0`+6d+#WmYz@rMTp&>oC()KoZ!(Dcbxf_"
    "SI>WaVVo+agP|lLbNycu7G=gVd-R_#sUpdmg>pZYy10a^A#PEeL%y^*s}}p9I_<i!S$eQ8lPg5updP08zld1#+@kQV6L~w9yh$NY"
    "kwe`vGb}8MtCpEL)Mu=qchu4od96CP`LA!Ety6ci+D(>(>&ebjeqsA~wtc#hmm~G6zPP#{uLzzjbpG@0@s;%NgM?LLAxox2Qso8$"
    "8*P|~xuqu>Un=txN%gXcxt*J-*g3{tj@b3z{f>1NH|{>6fBSHm1*7e#toR7(RB@bI`sswxsgeeTW^5+SA{!L)Evg+UJ*2sLvm!JW"
    "Hwv6}8IKy-A}HL~7dN|8qnP}_*wqHNSg77+(b5yrPx<W==eWodi@KfLE&#YgCd*qa5gMx+6m_2(btdUxA=iXA&xhZq#0@uoqH<~S"
    "ylhalK68J5#%R&H<DZD8Y@!XO4T`AwsT#YYARV%5>2cn$r)*6)>s*GsqM*At9})D0%|8)(>SS3tvxaK@#jz&)S$e!IPZe8KZ6p7D"
    "f<#-)iO4K!v4PU<Oz{2w_y4(jysppt_O}I60w^`FEbnLL4FVDdl11<!c!H2Bz%%1dCRo}WABm@ou?>n_dct#JM?w6qhCXfS3Gc3%"
    "TP;0Sb4;0!T6&^{c)S<2JC}SX=!v>4W1>I8bsW$$TchyTK(1mlhsxaP5ENAh!<_f?Ia)t6QF^Y3nbuyue|tjQxw7UCMb!gQrh0oK"
    "OMwJI^afOVf~gdB$>pG`+W+<=oZ(Q!rG4!y8cW#X?O*nMQ4y!MSIDo`v~T<W%b`(Rp*ck%qo~d=^xq$$qqq>2qM%VsX5+8hpG~cA"
    "bga~-UI_L;L$twp79A`$+ti})HAzQm%UjgptfYTA_^u?4Om!*!h2}*`ZSZby&-6d_bqVo<MTPv}gKJ`bs)T+jJVgJp{}AaSXUz|?"
    "ED@Wh#6H%PgL_Iam2oLZe%%vhi{soweIrMV8!Y#|u1mPZKFGkes2N!X?mQtp$nb?dp8c%IAyJc#8q~w1I5)M>huX+~`rLNy6#7t!"
    "J^U5!t1lSwQn*<i$g~{Vmo)ESq3>#TGkg(qaNQC+Ls2quAy(MA9eN@$xF+VXe;xNtp&@=SSGJ-ao}qNr%v*X;Zn$FC^#nReiHAl}"
    "=ck-jgx)C<zt%^)#R;~XrKP`}W2eB(=i5yuo9^&slq-E-*%-R`j3%!rL}F;jK<M@H{w#1X{>vVVN##t|qJVEnjpFp{+iEu-W8YGi"
    "c|0;9Aw@weY?4={0msRa%nfHPW6Ft}`s)!UW(z}qC)|Z>rMcg?FFu&|8Mv5@8x+PcW>&^kj*cSVk~b(!J53G!jd1eq2_ajIVO|6K"
    "kK%`>XA-s*g>6mZ=)YiFV-~q)m@jKa{*M|Iv}oqM2z@X2cxaS()S#emS2i}xZ_N$x2o$y#u*1IY7u6ZUmQjH1nN$NuPaRMWyC>=B"
    "AhwJ&d7#Dq0na(NA(9r`3lt8C3m<#?lbCZ6#cAwgMX!5M-sU#zrbYFfbwgiTL;<$f3UE+YuUafFxO{&2x+ha;Xl;!y=dj-htlTn5"
    "fDN_u|8f8H<o?l3E#>cDt>qp2i>v>!`#;P3mv{C5ddL#>m~`JWmjP^=#a-;aXzGyB6M37kmZF=4I$-=m4Yr?>Kg2jy8en_<P6wGT"
    "^Rc2*5!hhPggB`UH50pb*wfnj@2*mtL1T7yH1g?pZ$9si=k_&{d55$Im4^)e?KL3)(psl4eXP`wcziCNp4C*^ATK}qlE5Fgw(YdO"
    "T7YfpPnbWlws?|vfAId~%pSYJ$p~BeheEL$tQZF7wjYrL-t=A010r9IfEL?pK`_8qaqNHWXQ{zYh?Y@+UCtRb)*sg>v-tP=XMeLN"
    "VR`UMZ`Vqc;$FJ<5H<_3ub4R}afl_ZNA>x&*j^vY!8sQJ_WKcW?WDoD#I+;qoCMfsmxR13g0-rT&yc)w8HJ91y*>WH$ko)x_ET|("
    ")U=U@RXd4L4=W$r&tV_rrP9OR^^>oM&a5Zfx6fYI>cBu2(vS%fxA&2?lZZ9<=5TyN@KtV0+O$}FzjEtr@UUN){qoMy$({;=gJ&V~"
    "v4p-+1WK-8DS4HKSW0gAXTQewdZ`WWQSM_&xe?5n+}||Bej(0O6^>i8G~n{l{M-PAe`yu0Fkyn^QEQ+pmN721EVPIH%wWBf`*O;i"
    "AYanf*af3G=ibfxYD}D<(nh^n>>rE~?|*N7-S=X)gIbx#Q4+MgB-T00eJpY6UH{t_i)$%a<m=LcrL3D^t<H(tF!P)`iv4~BIkSDe"
    "NKwR>raqQ4#{+IW=N$HV5nzv(j2j>cusAnnwmxW!#ZO-r-hG0-Be0`jkFaeGr%DO8EF5mlnAqWG_RFyks)E6|{bvn>>X0XpPhW38"
    "%ou^3_*jaKW6#c&2hG#TuMNW$zE*R6LM(L|YGT({lx)<jr3On_QhCT)*H@fVc9i*8Vv9=~w6s`LY=dFx*vArgL2g5`7Hi6E;Fdxb"
    "d26+r$vtwr{=3G)$p0zA7!)=u0_^mz|0-_qfOwoH?OaY6taqqy&$c&=-186D?ODIm)F7vg0xT|X#lG{t_v@Mn;E12F>R^Zcgt0%*"
    "uj>c=it=6FR(}0P*dux5dz)))zt-KL|HQ{``nB^1?Jw{2t)EkxSe#}7_6Fnu;~$H>alaqIJ}!ez(gCb&eJ%QWPW}Twl@0vVZZVTG"
    "(hvWX3IYF%9&vKpw+d_Qcf!LN=+ZUz$Cz_C_}2}R-<O5Ho$r(FC1b<-dKxv=GL%;}_Qefm!=_yn?mhMbmEr=L%$R#T4zRdX&x2Db"
    "rMzxGG54uI=R4{?jibWHc3v<a3RK2X*+mhn6k_LuA2p8J!z(e>3nG~-PLmGy;V&%$tIDDXDIEt`#zKibFWK%%ed3l6&sI=X7e#QO"
    "x3=Rs6$|h+Sc5%>&Z&Ra6h+wPQGor*$j>w!7ni-R!F7Y}chefY@dGSjjunBAODbYAeCTUmCgYFs^m@`;-eFLlUQc5bEFQ(k0)L=j"
    "spyh-KMEGt$|O>g1lX^G8e<;#rp!B)N6elEV{u+(|D@Mg+^bv!J~6@K(Nzg0``^2HKtnD&ytnDRcRYN9XI&H_i-H*vdbPxVJ#K$?"
    "a(_0yf3ewJe5{R~zhfsBwxP89!As83<OR?LyJP|-dE#S<MaXQcF^iqdIA@?2pb;#dn^s?5zDS>(L#&d8D?B-;(nvC2`FU|wZ*jfd"
    "cmkB4n6^8f6X&Q1lFN3-OG-9Io<%I!Ybr*Q`dBJDJSvkA`-Qo4gYPA>LFE3*11#k&$%C~b*rNy!!tt`-UubY#k2j{{{(Hp1gYO-p"
    ">4fr@1mlvgscg=##jYfa5U~ZkTpf!dR@mE}+K3o030uHFeX~dR=V!ydouu;SIh$;cAMgdG!Q3WNmgC*YLzkTo`LO+Qfn|M;d=zIO"
    "`^MDlL;peipa}Ag)%j7sAk(0`+nckz&|NYt>K&^Cjc$fquZcJG+fQV!RP19pjjPH7?2@@secr3F%uNwz!S|9L{$S38hd&E40d{Y{"
    "5T1}c@E1uIGb8O||J+@iZC5MEPS1NN;(kedET>ERN}6Da`~lzFELdih0{ciV#1lqC_T>D0DQ^gn$3SrpMXYe<V<{dE{5JECzcv#F"
    "8~a#DAZMNR`N&13y{wxWD@C~o3FGnbVoliTa$99ScKd!qWRH6pl{J<y7UcH#B+OzXk`1}?{5@3^Zh<ELD&4V(`iXx9Ebjh}S(gX7"
    "g3v2ZVGM7P-#zUY>m6hakEz~$ke3C-(TjX6=ScCdt#==&>oPEoYAh3|jeJ96Uumnsx8q&x-+4ivg^s>nce_Jx6a9eT?s7$l^elA1"
    "{^KbTWN`%-E%yCS&c)}uCEx!f6q`J>_xCmN9#Y_aQ*>VgfkD%|>|lxS^)g$alj|keOVjKdDw`z_u<PdxKNLQeOgi<)9TO&V5u}s|"
    "_Lky9Z`|9t<e%eLiT9vDD$rwcHE{RUs6Xx)6VjjUdN;php6z<OLxcc4>9nsV_uyHJeJtgE(e}j-YaTv8*L2lI5hg&(MfXqUge1&^"
    "3>m>v63O!i)>uNBkyrBGxb7Jt;~#6;>Hg$|xN5T~@oWM6I1A8J6Yr9>DB#E>o=RX*#PTLSRvsM?5k?RD>N#;)h|Q9D*c*s}%OE0e"
    "QADJ#WqzqK{9{6B<DM5zD-HKME)G8DEIs%+7j*N_&h(r+v!3oGSSI4&hvuck>=VN9iIWifjB*#00TzF-kOx6kDQ<erq+5F_Sf<<~"
    "mD5`W*eS(YNr0U(MId4iI~(8s=S#wC=gafioUS@k1Zg?qiJ}gpcYoDGlg}lp0L#=K7<myQ`DDfw5c@aL`6qE)An`2EKD8)9+w@lW"
    "E&C)h3$S?5JPV#j87z~$<UO5}l6%LDC)owjwjbt99iyZ{AyqxH$bMbFzx`lUj}`@0wQ*M!Sko(Zvm%n9^7=lk8q~wwSdZdT;%h^I"
    "_;$C#Vm=@>mYhpRQevQLF6P@`PKj@Kr8gA?*?s!l>E*OjqVjO{7xUHTQ5C}{Eed-}qV(r<^&`zz)%R0S1t3R%!}t;thx&@Wc#7=j"
    "pr5ZfWBL#VD)*HsJ;++IieK}Rg8AyKL1C<wD!tr;&{vylNHg}K->;M&a$Du@_caUs0eY=<U=E<BPb2htz(abuDV9I><XZQqr_bU{"
    "WlDnQ<@$~+5PYbmN~~r$1Kg76g==z*i8#A9aMtW%h=)xVDa{H-W~E))o;)H-a5e473<@h-II{E?P{G1TJE@vHSVlZX4GP)8*u=$b"
    "?kn&W`l3PT^%(`U9j0~Icn($glkIl&pvy70*?ld9Fq0h+Vfftojco!gQhQAQu8FS@lbG$$q*LT(uSS-hDt~0Wj*7x`E&Xbfk_y$B"
    "%q%@qW;h<%QTna92N^zYP*{OyHwtywjbOBiqsWTIb_KvnkQ&OY>1jJLcYR_N3+;~C{bwhVg@V^lHMYOajil?s79A|a4|=FgMkS%O"
    "8oR*eVM5M5BgS7`-9Nk9{_)>XKvuZO?5{~;Wad^jD9mP2`XymWNnYqkQIbc8TmdF-qRD=er7-&lt$?}8cgHux^&}qSq(NZ{hB+70"
    "i9jGOHTyD?F6+dzN9|^8QA{1{!kxa^BeZ_4iEv5s-m^=(4zYI0uCYvA>L{xk6y#A!(v}{ID7CX9d=Vx_FDTqn7L<O=6<LWnZ%~-("
    "Wn_rS@ni0YszG78fjJAB4G7&SW}P(+5BdtT!X}-JN!5rN6f}wn#7JXv-ot6Th$|La0rN$gt_EpS`uk_#tsRf-@1s?sO=R3AcOjBi"
    "IYd*Wpzk&F*VHCJJB^HAQEb?n&yka^^U>@Y$XGDEQD5J0R@=!~^nc){(2Sbhl4;x_s8~@nUuDiTTTVf~ij@yF{{*Sqt#hmC@l2cC"
    "X(pQW0o{FOH#L(1k|*Z(HH!c`xruh6=c?G6VoHj_TqRlCPaDyB%D8Dv&8)3<?fwW?wIA8Gy2s#GMB3yQ+Pl=X$TJ~Srs#N!!Yn3j"
    "I(JTJJGqsjHckpzf0iEP!zl9FW`^A(4|@?^_eflw76#V#ToRaLP^P2Q?37?IVavp}0>d{{HmI`Qt8f>0>DsO;>gSW~e1$b1C>s<c"
    "UbL68hRh&wk=rg$uCW_)(Z?+oN((GodQ7EEU8O0xizl<rBK+IFfl`+<)<VLu{%v3^{n*t+5@LaYGz(Yi;{SfyRww>`w0ri_-`s!O"
    "x4CI;qiX+(uj5*`+@77)$E2Si@oxv#KXn0gk=TDcC%#eJQ`GFy+l9fEiS(sUXRi-#K|X5f!BLWtt!reOTI`l%VktD$q!xX>H#kGX"
    "xkohHms51Cde@>Bg+GrSn!F2o$`3+oo3!-c$ELN7?n0&Y!q!LQ_tS@2H1z_q4eG%erfouOi-I>Lb~VH-c6NoXWZD*WX|ULAt1b$k"
    "Z5htCwt71A^d85hUX4LZ|Ly~E26KN0jf^7BufH;<oe14wPAj@7oZtM}YEL|1#Mq_Xn&ZExPR`(Q_Vxlk&P@exgWB_qVi4=C>bm~_"
    "N6e{DJ6LQ-$}WoFfy~EtV!?+;thy+CM_fLq!S3leu;+}_=W!oO3xQhfwaMH#^b7T=Ogz3_uWOr;*_XV7eR!3UdNVzgnWXZPyakrG"
    "X|E4WHHym)u!gAKa!`g8qX5!-^)|30QRZW%d>OMcMF$J<PZ4!dxOC0DvuQdJ+&}x)Z)P}nBY3B5b0iI%ksHBZB}L(<tnlW%ne@}o"
    "22W_q3|5&zRye9W)VdS&JiISS7lm_C>S3R5b_+)C#iI@un{C=f;j0?A9Jqb)T8#a-8*I>Q4-mcqn|J*JueCLNh10eYn#J~>r4L~}"
    "IWO3o4aW0H7X|Y}5(gvpZSWy=I?g-Ty>{rp8ISX1?=K)<?duyB3rKrkzcuyYmkj^M9W1sxX%|KCQn)+4M<|2XaCdM`K5L&}S?qF("
    "V*?4(!*0KxO6woUehKGr`x#no@1_&GK6E%A-lHChSm%JF`c+m2*2>qkYc;!*YI{()#oh|P8iO8>=3zyPg6Eke!HDv};lUl0P=3`#"
    ";d05Bz%{m3K1mHfu13KxOegqBk3CyYv5*DibAqA>F7nsvT$E=VoBLn7r@z1;HVUxJ-Qio`TCtze?#d1pI;VNuMG;?`1laMM&}OSF"
    "z{;(`aAVe1pU_``<dRoOsYMaGlQ-wn*PTGg;SsAY3YQX|?!7%d>jan%dSZPpQWW7gNPVpE1Eqmv?K6k=7m!sdM_m-5fyV*%f|_m7"
    "!D6$Gx+t8B%5b)~b7pru4!l0uK4sj(o^h>M>`Rj_iqO41KD@qyY~-|kY~G@9PKZ1%y8bcbeoO=R<Mz)_oJr!V8Gn9~Y-9pk1lZrH"
    "i^<!>ea#LA#a9(zmzaaSOuHz2#AFm;ua6K0h<tOeMy-BA%57eCQTVFH!91IM42WHe9u~g@6K^+Hv)y<>9Op9YU>OnQaqntH81i1D"
    "9E1JR??^nz51!b(9dCc@CUP8J<b6P5e|`8Aatft^^U9)#FZHlrk5D&MS$0wQH~KEDuWLdwq@hEp#^QS_Zb^UKZ@bBi;o+)-B~+ud"
    "2(WKI5k{i#1Xw=@jl|eD{}n~>L*ipmrN}q96h(}f2H3ZlIpBNwevG&8W(*g#>myTTg58Pd2r@e7Q^}_Lx+csY&lr~`0@Tgusa3WC"
    "0kS(u9-zQ5Vik8$xFg6j;rm$B5#)8$lHYkEZ|E2YOMvB6-zp8T*TlHV$RBsI{c9u4iC9BXv<HZXZoN}q!$mQmu1n9(-94FYKW+#E"
    "P|ii=!58=EbJ|R<y!r2IZ7?|b!pCxZorG9O_>>-GVZwR1@Tq((VKsOa8Vz<y_=Icjii-d{XME9~&0AwRAE{@7?(M=b_`Owteb4v@"
    "vT)o#Ke7=D-~P3~K-hNyRvH1kyQvSwaGpst8U-ju<c>TQefRA0*9tP4ni7jG3K#OD*vIzEmkq5?5@2`h6JlTDE*3hoo`1lih%fc9"
    "lUXg98EoofNwd`Be{npHu|3VYC}Lj{AKR3mB;tC$dZWJp?M~{Wh<p`^2F3w)@c}Z!%dCqcWSVzX{eH@+2mYS^UYjr*IXH+el#T)*"
    "7J_feXtyZBiRWP{HmI@waXVbabnuw>egO&cdRCs4zMm`^f$y>I?5f}Ub&w@I@jLrK9lAgRIZ#!8NOAIVFKf8y+rUD_J|CKgZ1{*x"
    "sn`a~xH!@P`xf)7lvNi+jF<)3<ro^#GimqM%pbh{Jtn+(?ROg5d+#Uyy<h9Dpb!(^Lc9kExd@6qK*Fby4#U;avHfmR-QIn8=!z_Z"
    "Uz;-Cq$={U#Kn=dRY?u@3{0(zywJ8q;mUyL_TO7fe(+0UA4^@4eyB^XfcheMc8Q&WWDk%?3-`WvvF?{+8j{Ao4PFa>Dv8BQL=h|^"
    "WW0L3Es7Y?pX~?vAJB+#7exdUy;HLsZ~wYuu8gdM#b%pyQMiA=Ut6=h@^+?P<i&=Ww#UZHsVGj+w9_t%U|?^9_LXxVm~G<Ubnkz1"
    "PIBKHv#&V$05<Y1!5$WMzKJRo`@gfpojGX`!?i`uA!(C$QN)TB0rrCN$yDKNaoaErf|Xd#xkq0c4wqjT{x3UNjQ_JPidY$MwzqRC"
    "-#G9{>?=_|_@z|`i#;K1ubcZPV`(uDtxw)X5qU4k09I6>n+>D|r9li@s(-(Nk`R2CkwxKx!gK!IpS-5riN1U7emavkgV0hJT@(?6"
    "PCe|oIGLyNgi{<c%a22kH9S7NpU$^GE{Hs5j}PnNw!bZhQ#E{_m{eGro-tN~x1_WAul4BzR)eQp$!qAzjM;jRZ_m#NuT&a%v}(1V"
    "@X9tFwB-#ZmFrbCg+qyFVyTPcJ0NzTvH*gM%BFlM5~WR@XGZA>g(S78)hFiBaonJYjFH3@I7QOkCBkmMNE#0QjYqYja+qKE^C^{K"
    "qLl+}-VV;jnl+)BFpxT=g+@s$Mx~ZPK@w6keAdsYgnxC&>>jVEY!kJ+O$3~<Lp902kHXXYZLOZiE6VArwzEVw7k5k;s4Yjyy)ey3"
    "K9F^TN484goD(B5t_2ddMq+!XDvHj7H9Cw$xRBSrsWn>n_O>1rkGYn%tJNgbB9J`us6}0mne|V6pz+{Mnb{Tr99ot%fZ*{9lhmZ~"
    "`hF>=gYk=`w1w1`;I3u1BpQ<*7HJ7G^(qst3G+{HR}xYrL}k^WFy4sm$}lh2B9lU+s9J|K<s8ZP<65><e}O)09u~R|+HYh;r8#T+"
    "TILP$d^*}&6zkynYvIlMEHhpaeb*)j<lPcmfuyA;-lrJU_fP$DOhY?cc&J+0{yN@Uf^z5=w0xQQ1v=kA`Psu_buijFW9yk}38{X6"
    "&%yP~w2;(x^_lsiv_Uan)Q*LHkw;J5vxTi9RojoRCj4gQeK_`YX56<Y@NMhS6LQ;3ueQ$M7hzG^R8l(XXX*U&q4J@TZJ#8lp0qiL"
    "8r2iD6{5C_pZ+@h^WHjCBg;#c9v;P3K&nyiP97X3%0_BRNR5|iSEl{*0cMbOD@F~f&k6g-azz3y3j3nSl`5@KeOJ#As?c?Ky}drc"
    "R$KS<bzgTqI7-p*&+AT#>HZZcnmv8p*CYq{P4$Fdt0~8Cc8{i_BzyYRKku#KCiHPj53WFFTTT61&3|ns4FALpis7GjEQS-5f99R&"
    "$>CA5mY(3!Tv2^L{2)q8z|E!ZB7rI`s+X5|5LH=w<ky#OZM6OCP&wYN>6deKk1BVL6ot<%wR5|lp5wfyu7h7+*1x`eMtLu@ji{v7"
    "Q%_SGKxuhfhuWhf4UX7i_g=e$CnfD*AvvSBfTDm~AT=?anqGLr1S^S^iS1bZ*PR2X)M&YaTA=ri$fzuBP|)pWtcjZbem3V;J{#pa"
    "!>{8*R?k6fWp$pKPx?B{;3+WY`s-caav!=Kj1}{1eTwTaW@QqK`tvEnjhRK=tU+#+8Af)7o!SBi>5UJ>(&Kk=WxuHJE*nCrywVC<"
    "#7>#>^6fQoBS$uiQc!=~FdAK~^)r#PY&4mor6=xjhw2rXJjf4)liLPGte#4zZ#SZ8;5Unjby^g$zxKOu?a{1x;!ro(nwKp-K8od{"
    "8{*chY#>t9t<@CY-$XSoQPM66d7D-ZYWsL5&vO7x(&}jj1+AX$tkT0@l*V?HrqK`nT~^0aEHuNYrH6MaD(!b|e_Sx9!|s$c9fQt="
    "M-Q)FVZ5n=dNL#KHRCx~6m!?4O)Xz$tn^R?;K9{%GYo6M9$vkyrN^aZWp}n;vvEidtfB@*YZS&mZ?VvK<t;rfks4lF{bcTr%2rW+"
    "_W?bFkyoqv-3Lr7h+BGMr?lkqdA|X~pnS+16lT|#Ej=O03yb=T(O5J{{rIDJx<DOFOr^-87zt+UebuO5t)#&_x3Z}3N5rSeX4y~c"
    "C+80x4NZ4^-0i<`_-IruJt4$0SG$`u2MU*}_xK|z%G`(x%yCiJvgC*}${eVqrN=i{Q_dcLyq|t1RA0?)e!Rw2Us(Yy_Vsv8?Nl=s"
    "cim`lu*YkBkBq=HYxwjBeyoh*7byziSUJ3rM^CJS;h*CxX-tXps^+;F6ypd@6xAsPdr)9%evZ-;qofw~>=GL#Y3T{B)4APjzds^^"
    "0{TSg_=eb{(iLJl{vkeLVjXm6e{=$uhu0x(>G8Q~X3p^s!tpL{6W7<i*A;Y->za=CjQiA8k0D(jdE1zPbP7f8Q8}(o7*yHzmuF3t"
    "rXtE?#<Xl|BRqM;s1|Ol<0av2Y{oiXGJN7tzn?NI>C#i*tQfad(V(E4w0Us-X2k^fnzY-ay~+H8H$v=V0fW>V3tscAc`|Tq-=s*P"
    "@?KfsLB-hp!tERpK4z*_03iZ5Wdp=^Eotd-&7^s_5f<G&tTkmVJ)t$(b>rMns*}8&Zckq`_kM0sy}Zq#lcm}C2F1Hm$`*^Tgx;{V"
    "_=TmDK_wPNX=qxsutwnqzH1sKs0+xvvUg=okLcbbSK(0U@o$MOKZu(VHvMcxL`C7Zq-K)8Ty2-ev&6E5mQt*5Nmz+8tZPx*cQb}{"
    ";|9h1Rmu()iYsYpK}FRZGMg~wYWt0dxoRJ+C_Qn#j+$h9E?!x=gSIbGe@Ku<P0IZjOpxX+Jt0W#e)aP+2UU9eh=5RsN>{j2>L-6;"
    "vNh~`3VEM0dxVAB%f0Uo4r^RhOHZ8Wq<O7C9ImSLPy{2HrAQkr=D~2^g*b0ZS6V^o39G?v(8X)UVeaO(nBkhIeI8{{kYH(6Y_TEq"
    "+t|HBF`l9wlSGla7el-EceGzC$var=u8dn0bbpmCJ;Cj6mv86HN)`=@;Hc6HThZ?Dbfz+DQ4qJ6Ej=+eyV~NfgGQ-ZdLp@~L9H=~"
    "=jdl+h(6C+dcsd)cC%KV5r0wTG^LvU_=*Uv>UDX2f``t{DQHpHDX3a{!n!f?<a!|`yr4_DXz5`dvky)`o!!6KY%k~9q#KG9s~+{|"
    "Q!al%b;}w>MO##i)Tj@0#;8v$3XgzPZnNZBA2XIZMQap%F_{>>ogtC;Qnf3ON7Kv<-FICdnI4oMq0G{J)S~`-BBe0ioj^e4UIT>A"
    "h!&$(dcvw|Mj2zH#4SC3&t`UR_p=QnC9(#E%`Iu^@fFZ2(|>*>WXs5D9W@FFlA2MnmYx`;u&4#5Efjf6Ppp6)1^3>YhX9d9Eysv-"
    "jkR`x(i4eo`bDeV+ch4PF+n#o+zpf4CN_9!p9#;#bhfG%!Sk??%Au|&MG+FrEdE~`>g|S&)c<uyysC&?MEkEhJR?z18Y*4QD5kOj"
    "xP6TS1~2-|qH0x#$jnSy6hf~zl+qJ(D=Z4k|13RvTn#JTx4gMwvQW|ng{?q43Lz-;ijfKi%(`jVZnYx#XXM=GHEQ;VF_&_SVltX?"
    "%XNa%^4-MMrpEs23-@(u1l1_OMIiKQnkhYQG^tU%uZhMW%AAhdGcE&JGnBrriT5UjOQ`s|?pHw>L}glRf$$|3E)21LPQA`Z)R+7H"
    "=-2H}!uO~y?i%&=lE@8KZ>ORVdR5_+o>&KqB9odbMM+YVd0oZar>TdXLoavgvpgELDBRIkL>`KJ;gV+FH|~2~KKK$OZn0}7ZJ?Gv"
    "r8jP`bGH^v+AX9Rll`M-ZurH8WU2i{Yub669JYQt?>)az9ry)}WdOe*Ee8E9Fc66tYO#^}k7L3q5tsf?-Q1s_b=T9Myf`tul{7u9"
    "@m;X}D?My|_0%I`zYwLdE0d+aaQGei5ciH+F5(_`X<;Y_#GfM>|56!XA;(wlLDtZTE}XkeQN3=whn>kqfLfwyVA4y#UlzxNyT>>6"
    "?WX^!49NuPytSf|XOhYX5=nhot*m7McKX06u$8_VdeZ#a3r8#<TZ5|s0-Kw7SA#UKTuz2REiOF9^BVB&B~CMs*lW9nue_~_ufMQb"
    "Jt%+Dc;wN4p^}2K#N*YkYk3fg&(mW|ZErL*&#E@zV~^f6B*JxUZ<m{=PmD5<2XKH%a_?T=jqmQC9?`ELGjDyKo!p;|?_X?o7aw=O"
    "uLmlg4P6!<AMT!=ZGT)0EVwbyT1G-6szu~0UAyUtIHl{U9?zwG5V2q0RN2s&$Ip0PK^l7_)?fPM(cY5&L;F=E-Y-msmsh?q9r^Us"
    "SW(*E`-jT-4=H}$6(gm#r_14~W{G$7<eKL6%p&y|>79AGx%&7wc{ukD^1BcHcH4t$wl@v?)S6Ru;*obGwHF(yHrsXv`V0FC9S<^g"
    "+`;1Rrl`uhSSU_f`Y6Es@y`A=lj@MhK9J50F3LW9ZxfI~Az$tJ5oDFBQ2>Peu1NqPBA(t@w{uAkTg)DiGm#J3QyY2cxOsZ)?!VUe"
    "zkM{Pl|24g`>|3w>Ff9bY2%5Dn!diOhUtsMr~h0ZYC?fYOAjj->-PP}!^73*D7Mi|2dTG!(ak*UY;NB246BZnPhV@`57?4P9?(C#"
    "eBk%XB%r@|Jw#u+w4$1RdPXGhWKL)=m`X>D1+gR!h^=h={pfx{y@<>j6y}Te=!uu$I=Auts~ch+suqRGmb|6M*G-H4ZcetxlieF8"
    "1yr-L9gr2>nfhQGIHd>`Heph%WBeUTVUrRC^@_>YGA?%!xlbMu&UWJtQWV3+u|-`!V)i0$P;@$OoOH05`?sAZ=Kl3Y!S~C}O$rGj"
    "Hb|be^mx$#EdcxYPF#pJZ>XEa)M<e-YD%5t9g$HZTc+id@BYr?*2KdiQme8bD7|%vG{uoc!SN|0Q4K3Td9*$Lfk{-4o;b)3Mb&jN"
    "4xAcwKc%X=MOqa4*DaP|WvX3C&;fs7SlLt!DdvoerqUL87t|*#39xYV_?z^?W`BtTgi6t@w1)Ene>!1qv7$v0aX?e4cwfKT!PV2T"
    "mW{U!n_*>ZSyN9S)6$||jTs%l)y;l|8E#r%SLunlxi9*Yua>65v&MdB^8B?9t#qv=Dj!Cf{klUH$Oq?XSCY~yQ>`RiqppvbvC;;`"
    "tce@zmROVA){x&2&od>9z|~i0au3p2d04!f%#(zuL1DL5+|m;=%FONAWxpEjV7^wOC_JWb?ySP1;9Lc{M-n?jq@IkS&sut7Zsp%X"
    "840kj@9-eU=8EEqY#4W(ps36)<#TmM6Ek#UF*SK2H7+K%yJs)OO<I55L-)SnK(mG~eh}J4WCNP!MKG2RmPai;q4~H`HcWj#ld)W*"
    "h<v}1%`FrZm}YPMZ<d}glx!;m{600ST{S3dwd0nacv@~7Lx2giacuima9UYxR{$vhV!p-BYWMDjxdH78a8^K)G$>5wXDvM;z3sZ;"
    "u2k8b%JL^ygr{)p(Cgech;l7Lm`CVwWM_z`pjS~#Pt48m&vZ=4{L1D!)}ouxek;eTH43Q2ZbqqEdVCa<c_^sAn0FcKsHra_ii=dM"
    "`TevhX@c!k+@c6eDzzvk!$C8sEean?b?o0yi921Sab{6(*MyXaM-2*-U};NFSPgc~30=3eIpK<8WJ_XEx6~^nGuE5&ukVlg-FXiB"
    "8BB0iQ5f%~Ej@8MbQE!1Gv_^16j<#uRu6;ePxP>^RXLyAn-%vSP5nPLijsJGJHJ_>#qQMq^M=SFHz+sCn5p7k78Z3(?T$ksW$r4c"
    "Jt{q}IgH#o;F*n;%{EsQHn*y!C!}0#QMiR(*@wD<y2a+EnugL7bF;k7dB8Hu+eF5A;rvCjM_|=@+x4lYe>G;k)|$s<v8K;8<kDBa"
    "sG^8k9Fd}keC)zC)T>eT+#Zxda<iD7noZaOK881RtO?h>LiOa?)%L?VV!{~42qDBf+}L)1dpg6cn53mAv{2=!55yU%Y7N<N`|Kl8"
    "6}fVj>FgtXe&d#&&;e{0Jp478*(S3NZ$A-nkkVN|rUx{}3`I+i`^hWqn)hk<?1a&f6N{S6F#RNN=?U#FwJ555M`pi>u$W5cgL=Ed"
    "qYOrCHT>{)Ege^hu_8rrFBvs1R->rbf~tL8ob_9~4x&m$5ydeoXE)84V%g!flyx=cciTCjAJ!bJo~y-?1cDLYol4`ycsC)0q!C|c"
    "=@zHN=4PWr0|bk;N$>y2SWJd*7aQn#e&n>H#fEsEA30C;!UV)0v_z!cU)<6okFr(kP<s4MFI>mTlOwHR!lY0->>qbTnN9U|C<;Fp"
    "%6soVaQeSmjx~yjh$R|*GYPS(QxUvWcv#~6x_K_KGBRp)Dm~%bEEI(l>M`d+_xFZ-i>*;GMIrQsM^8v{gIY3qS%vd}Ehl)q!@PPn"
    ">#&^uT4VA-{gX;h6kgW3O^K>0k@GkH<Am$rqx%0pPPlteWkrpmG&hswxO;ymnH!MCQnd7hugs#hmq&DsM~w-3SZJQw7h6$?mY92^"
    "5PEN^DE!^GK~;+4qGo#SzW+&hDGTQx*6zauDzd9IW2`5YVAn@bPZ`l;8+xV@gW4LapSb@=;+y8#te_Z=w^qfJ+HNZ*F0cN>+qt~^"
    "Aokbr((MvQnX!yCyZy|01=a4TQSX_T>FP_=C(p!PP}qO^UyLoFCu==Hi)rhbs_7RmvGZQG^u!(QP(U{sBlk+%MS6L|REtd;6sB(!"
    "Ej__+X2pIm`D2CE#_ylZcmH@QuYD1f(m01(2*Gcr+w!v|muq3}iyDO%{WF|q=?TdoXI#`9Dxzw<F|~mP`5p`F>$dd7D3L`SgQJu!"
    "J>lzC)cJP#L9DIiRI6}MZ)43$Ci**6XR#<N9csn*&5Sx&Ort0)3h5*@vd^?FJ;7I*MO`yFU2)=iwVz2N5<oO%%J$Rw?)N+9?YW{p"
    "L!MY+5?zG#uN9R_F=|kl$?wtQD!sOhpRU39qv5*BLS8YC87;r9p%QkH)xIn}(f2d6D8_P+Q-}I-f%!d>mY$eftSG{Yl($s5MZH<^"
    "MG~qOi`>+?Wg#tp$Gp-l0wDWHHjjKbXB<T~3A_Wxcq|Ek@K#2S&4?gQW!1C#hNYTsM#hbBKbw<Fnkb4cC{fuYZ6Avj&-YNop)j&>"
    "w&4^o<KC<X+P*tw-qNNP1vg?gNgAUT_1_aLL!)dU*e#j2^u#S$C~EhPumLq1D=55DWnm-Q_isPqa#d<$8QZot8@G#YU9x{V#C}Q5"
    "x><wrSMQ(ptzLbtL}pvXI1TeO_R^c*&n<n}aAg1Q*N5HY_X_<xNmBtoq}D$*c+miXxy80u_-fkGjStMt`jmvecNY(?aEroLthDqY"
    "KkuiHBlS)TeVCzi==bC1_v`x<`f5wxukdzoJIW|6Q;P~~IvpCN%G@YD@A}}{Rt*Z<aXYJyrFNLx^>oZ7@C5Betn{5+yTiYqTl$NK"
    "_j*)CT208%Bd2LJva34pzllD$cQQ)UpdgMlv6x?9R^Y56lOHZ7+qcgLYj8b#39~^8{vftu=BI9dnsRN}ib)_PYEg&lybb<B-2B4c"
    "+8P5`jhI{PKJ{ZjY-;@qiw*CZe;T-Ja{IlwB$R!R?O6Q=UV~p}S7zHQJu!ePjZa2V+aKfI9}{^3|Kf_7Z96Wtsx?EZ=iFk!RTY_O"
    "=iI4+b?_XiG!yzS#EutLg91)>+U!~<!{qR++*kA(@Ex30ZX=kA!X%;H9Z=?EMnxC;1<ZRQpNj^CjFKA{hoQeC#8(_OC~SpurN3X?"
    "F#KFJC{9Y4kY@+`@H|b5LyH3FM~*Xv9+gE=Vv0G`B9}M?xh=n@DBsHXr+rpN&2NcnO-hf=&D@NUoj~|X>(I^?RblCuSN{)g##$j!"
    "1>m6{L^SiXbaSiq((}#kc)?7gYO%;Itf%$sa(8>qoYt~IJv>TQOF|=a>I>qJ=h&<)y{UtQYr;i?!bUOjbA7a%K80mSY^AP2VWSus"
    "vOet>l^v8+af5;+m5B=oJ#*u0-$O}TqV6^0l2sIRBdByT^b(19G4qQG{!_n>ab!Eq2?W2|<lvMIYP<R*4#|CWcm_8&Z+-#W+``iL"
    "%8d?gZqlHz%}p)+>=CoMS%c!Pp-5r~7F(NFa*u!8T_0^<d_aFej=c8^h(VWl^r+ZRtzuTA!oba870ZosJ;vxQKR_3&<RhEk|MuE1"
    "iME%+HAwyI+s*cJ&IsPBL1D^UV(H&sK1?r1J5qYY=_F31$k9*Fm{V3XC~OxT{bGil%F5B-5o@c)wLu}Hlx|kW^^J@YB}J60L06m4"
    "fBcksr|8wA*tmmzXr78n8kD5%J^MyUMNt=3;BO|lN@lL((xPS`pj}hLyr#dM<B}>-kHluu?}{~`ltv~*q9{l@smph>*)2{Gg(p@8"
    "=D#PV&+JONmoC;1Yrl!>Wb}9@s^jwFVTkapDXjN+-YL0o*fm!vy=4AFw~r~rS8Ff5IPcIIw;%Gc6X!j+!nvidwdKz1kAokgJyvQ3"
    "skY)lN3>P|7RVP!erm<+$7^J5&8=tXpKc&}F_u%MuQ!yrTZ;yT&8oEYh-AyG<6`^tN9SSDp<5u)lIAAVK78wCTAX$=CcZav%|VW@"
    "w7BBn5cQTR@kif9X^pS2{5YdZ75(4*+t#A+RazlGh>1;8`}Fun&2r4~Y*CQ^T>IS||LB*FKMYA)2*5>|)|5VxM5Eo4#r^qwZ-w4L"
    "*H+&C0wmc=OTRv4Tr_Ee!Zh2wrH38ArEX9y45eemW_z<{G#NWX32Q=HqN7IwVZuC)zBaNTtuj`6&|tJB<xQIsX7`H*g&iFG6@*ol"
    "TDwM3*xEY!^C|Z2k)^*N+~D@MRg^Z+fyRm(6lo#W*rdfCDBV8@cZ-j!=#rq4x2QF9Y$I3T*I@tFgx%2BV;og9oP0gro}Gz1cft5)"
    "(xQQL8zhY9CVcxDV^lZRj~RBT4FkNKV&dIaj1>9<6=DaEb{7j7Xd{Q3%$PN=Eb4C@3hmdaSjxyMqfGlcDHiy;MBAFYG!gm3Z6F3Y"
    "MBBlSQRUV)sUIUTdSjZ|-`|aKCtj@*>nKnAFGmK%vhAGsY9b8{UtImVyFpAR+vMfdIes-8Qzf#fZ*YvJR&P{x32IP>TpexSoe+}0"
    "oy@~O3!T#p`$0lq%8(z#;#_tOK_k(8PHZ8ruoWImiB;|Quw8=!h-alL6TBb6q-$zXuRuqo<z#tbgv6LCH>+CZQ)Ro>nJM?Ow!_e0"
    "U~?hLtb@h2(yht&M?~gQ5jQAE%8ja)9#q$J*J)S1J+P7=Wp*8?h^p<*X;4_!kliUrF^(HqdM+=iALMYcy4+U~L6BI(6N<vlzCDa+"
    "?o(!E#i8oTgG#=Kg-i+eE$^rm$Qu-5P>-BAk{nm9ZVl{?ZD)Uawp*VtrzUMs56`W1UYFm#Kyl~N$)Df8fV)|Y96kIMMyDzo6qFmO"
    "8si@~Qt5Omo+3g=)w8Tv*h!vg$Cm2}q=VJ;YET$@6HC2;ZU^<0UQduPnK?U!(i7Q?@-1b9!W<(y%2ofl!B9q=IzK<Hw|{<Ol#sGP"
    "VJl$h|9o2C+RU9;H7HKz$m(^m&^%RJRupg5+E(xNnI(m!5fNF7MN}GXX;jnqink1GccG4gKR*!(kRo2928D^ESm~j3VxdngJ$gZy"
    "&AnOQPtVyDM;o(HEaZ1J2jpfWE!rXaQt46eoJnXAdM>(JH7HErN0xp$Wq2}gP?#svu9Z{|fRg9!SHLk}omJ7Gps0{??_XvIO-otM"
    "6J8se+KjvYg+J~FI#dpcGLzY&zd&+qZ2jtgZNS7=tJwUtxqotms5Gexz17ifdh$S)g}N+OGcGM(y{W5D+tmu&FH4WREDTqa4GNPv"
    "sig;0CiDB1rC+Qu_fDkrkereEWS0K?43iuBy{rB^wV_qAJGcT98Z|>k=x>;O0F^cd1&vbJS?%84Fy9h2C~Oo<f9SR2;1|UmEVidc"
    "ey+Yqu}5fzv89Lee+;KN6qp;PI>7A&y3HeJ@P1trW_9FD9)sdnJLzDd6RPW=D8!*1xl!OCf*GYnVRxcALF?yG^srW3wNdr@d6Q=d"
    "jgmSPVgQOvjx7D+2y++MuYjae=E51@AEC)4!j_qZAeq48_0k5f6C`jfDv<4fIUx^M+MuwFu#Fu%9qtaQKw1y{@!hZ0BjUc3<;r~^"
    "w!%$kKrEzNMolL{LS4~%kG=kbhlOO(bP_~Z%U0)pe0Tq!fX6tq-cjk!iKQ{vnpD!wbIkBb-k|#Rs}CQOqD4X6mDtXPuRzt;(f|3B"
    "5#42j8VWJcQa#0g_TjI~z3!01KL}dKvK{S*L))i+S9;t{t>vU@6s}Xnk>(@_3JDh`?YDsW8|BC@CLtbWl&V2t4DaYMM`h(2hSmp4"
    "tf#XxF3mtCn1QnnnYhSWEOa(q|4_^<Rdq$WZPuT5dqPP5JOE;2B^Gj^7X6U<ru|1eEOgt(7G)KHzmb7fbC<SAsDI(j3e#%r%AkHH"
    "Ejnjr_-l34uedVwL~a!M*nR<`L2Mjgdu@ykN{`f)XLML1KqlW?1=!zDnK>r`7I!jdu606#U2ITn62(QZN481^G3_*fzbB#zTD8Do"
    "C&W^Vd)D9LNxx#=;W@{)5~;;b`xWg5zc&l8y-ret*gU{;EL{Xx_(C+5J;HH&^|A)B#Q=8u^>jDBdRR*=ZS9EWclvd<2j>v%*Y4Tb"
    "gChzmi@GR+Gvff;tM599O#<x28MDh}fQ4go<~|Luaw33L()<C3nr|<^FrqRFu(*<zMxltF_Y3$BWHiN<|D|*M37#1@39uLNoaL=|"
    "6=Gi#*kTl5@u+KM9}P8FiB}>o(~GE!f=5)xT8o9HtKt7Nz@9VwA9<_v#S|?euu*`8cSl_M{&_dmOMtVJj{Fm+D15}C^0ED{D+4Q>"
    "_!35IP(Ttm>!R@4`ZuQ5qagUf<E5`-{I)fUP3&XESRnYp$1d@k+W07v01LV<qY%Z(!_>zTx=<PgI!TSi<&x-8!JNfiNvv=<XPhh2"
    "DA0wpG6SIx1mhCYNxs*|ej~Ud>#UWj4gqsia66MVpsHZ4zKO9$Wou{Mua;jR&TkQ5uc^Br_-d(iL7YK<&Qw5oR3x5sWnNww>mc&6"
    ";w>lSq>nviEQ@qh#y+-Rt9f9pGG9Y5<pPER&AIDD=IDvKI=Sm{uh`lIfNwpcK@~oBH@^&0lxtIh5Fq|fNreI8W=W$!)7An7gf15c"
    "*!P!={K<SQF6YGqR#pLair7JMz*mYQcru*rV#cg+I9vR7kX6ckEFs|~?C3Mb=YIdw!O{W#TCKzvhv!Bn9!G5^+sB_p^+jI9`%3R-"
    "!l{vE9$@h#@HF%qZ5a1U?ppXYSi;kl+P1k3c18%g%D?(+?ED*%)8#9Krfvf>=U{XDjSB~vIrv`EAo332W<&6Xn92SgZ3u&?#`;E_"
    "){%Hn)JPG9Q5OZ5YfC+qd;55{eK+)Q-iS4ye$M!oV_&tfl_dyl=40=F|G=n2m52SvIPqftqzm@@5rZv!Y`?w5&`I~4Zw5=PRT*IM"
    "dMvqX!P#J!jH5LQ)`~glaa6@V7ICA=&L;jUt+%T=xlkTsJl#ltB3#YR0;R&%*?_Sl&oOIjZXiK_e}xrA$U~1Sp8nY0PM9w(d@R1R"
    "Ms4#X#?w1ksgUZ;BTtrYpS>K?uCwq1P4N(-YNe+&N&l3K*F$5)Q6L77zwM4c_uH!tF<#~It(Mmy^ap?FADqj=Ge`vshXV{Y3$RzG"
    "4FCAc`-4y{g@3#`pB#~El?T|(h8Z{WvHcFYgX0z<_MG93D8T-4$4KCC+&>vNdy$7&#;o&?o>u%I<Wl8hiJ(u~!_FQt-y5uzRNlbn"
    "?1fNGv4|rE8|?4ya>dL!SZCt45^T6ux42U%Fe(qGB#p0#q^TJCK{Qh|4#F-&KM3SsMR5uJ6u$ChI5%AS<*t#gVoi|>LhAZlT4P}s"
    "gq*An7I#6&_j+@FHRdF?e>z@`ap`BiH^johO*7}j#}YboWSeWW*k@<M#m6EqtRwWtE`w;ZBHYWVEd%cT&XVCP|9hWq|Bx;K%r*sZ"
    "LhBZD)!(KG!Inwqlg+_|w<+_y(^{8<S?aWdC0v(r6j;8m&P8J+d?3NJnVd}f8mPf?nb@OXsR{0iqrh6%$N2d7`ns_^uBRkkIA<b}"
    "BMtN}d2auj(b>Xr-w`$3vNFWp&Idg(X=g0LCzjeOD;9hDnlY9~fsUt7{&5dX;;rp(U-}J>2eEO0#ra>biH{}h9l@pn7WTCoY!+ZI"
    "UNhJ{z;f$c_*lw;U!>k1(N)Nz%s=uq{QBsAyxIMn-9LT3+c1@#yeN<Tou@CE5TwVYm-FrVf8y`K6EEayi!A^?89!C8Ms0t)f|6LO"
    "#7E&_M{^RZ0E>HLlJMfzA`FC7_c-%<f%|XGxM_f8oHN<TANT6l|K4oJ|C^|}k^4hm5s}l>){<(moJtvtd;jKyaeR4feEs7gXOzc*"
    "pVmY`HjV;c@uxMhIB^tcCR#KD$NIN?jm0Bqf{lDEm981sHChmZ(3vwIi)%z?+$g{j8qsLv%O$O(fuxxFx{#uXd&J`kt&c%qD<4aw"
    "iPqS36kwTE3MAXjjEPL8BVSL}8X5#Q`s04%PEauJH{!ldZK*4V-QcE>Su20s4RH$6&^@B{LkMgYU{_4qvmfixIwY`elUKo7vAs^r"
    "ie<qs5OJ|M<PcLugxIOv$8sqdWw2BC=gbQ@|9k)1aF?d9?f*q^h*_)D#}e(m#9~bX>~zdv!*OwKzt&IuNWp3*u9(|3{t_)I12|_a"
    "_)0qy{WRlxheFGk5NsJ>sd|Q`Z{U~)Ow2JX1MFhWd~XL!xEB4lJhu1=60Y^HBt;RktpY6d79foSES&mct|XruSA@nZ2j3s}3-^dG"
    "O#<wAK^#C|)2^|2h0-iEOtjbtaSFUWx*dz@M+h8moo^>xic#iWg}2M?_-cDL6|sZlCHnjObuEu=udf*S>>Y%!%)KD`vnMpx&k4<;"
    "J`TRUp!Ge7IS1oXc`1P*wth|=!#E1oN^6Y3_VUQTf2H2Y7o;&zAeI${zex4{ir*jIPt9!t4O;F25<Xl1OD9~StjEl|$2Y(J_Z_pd"
    "m5-H_24bxu54)0?|8a+<>g68L6*(bJP#M7SULkUV{5jv@&nV2a3m+?mR`AR&FFVnePk~j1)N|b^cE~p_^9<I9(Bfj-uC&F@FPU!)"
    ")|T@~B;oojsf#{bpC$9G#<MJJ85sgw1lX@k)|@9U43^0t^?Vw(TnupK`Hx;Lijd*KmlEnw7FfITh7OP2CxNwVtDO+oD8S+Y)~q)!"
    "RS%&vF7*VvgQYSXlVE>|%CT7wOXaM3_NFb6f=6b3Y4c>Vy}TLr@kXACThk+t@eL~KqKH-XzHU61cku)^4Y1#sC)=JLBIQ|dEm7{r"
    "D!~4b$7{^AGapVII+=E`T-+=5Dp)Sgs;$B~Q*Pcg#NyY7B)x>#;kR!x&pe=CPZ;&X-_`|w-3Zou<|EiO^U~HA4q}j=FoMPBhb32p"
    "C&X_5U_3Ly(OVLa4$|(NMV=7j`uy-^`*_XlQ50bDV33?ypRc}f)oi?QxnRf4)1)dKm%H4{0852AI^WBsxP;$}zq8Aw*0zV;{JK3N"
    "#6{Y<5jNy;@Ta}mejr{Sq*)nYsfu=`zto%EKb{i)b1w?Edv=0nF`0OuH|J+(wks1-d&j^2o}G!4^X&$T75WVM>~ec~#4uHWC7HPj"
    "u$=9ahuA42aN+=a#WeQv-d_mzmMN)J1moVH)Z03i)kgNni;Y?=u~tQZJwIby-`*ZgW>VD+@e5_)kyjw@VDZh68Vf(JF)xCP09zk<"
    "<SAKNc2T%IPlMU+o-kP=RWMuP4iZ)jR#>=^&`+`ei@V)q+z^ZF34-;G?c_6Y5eU{_tItFgxY+g?Y_XS=kr>Qb;)Aewj541$J`+hJ"
    "aZrIuunQ*D)8F6Y`Tc@PF!Q2{(p`6T#E6<I#4;`^|Kv(nU*<aS*ZFwKJv#9Bx5l!CDf}DIz?o@>OTA$VQ+P3JgWWJ#pFNh`GvPQI"
    "g`bRT`vx0u2%ZdYw9q)j{$O@F;4bQIoq>m+Og&DKJ0j}983qeijCoGzS9}sI^_(ybSDQ+`&XN#IBnJi|gBpADjoGGft+Y1{A%enP"
    "W}^0HwL>1m-NnKo;c8P>a2l*OVfAO-6{Gz5=99|~oZxNYlR$_ODf;r&9qfXccKFqJqERyHt~M9449CSoRB5PZ*4P=-d$b7W{Pq)9"
    "1StxKe#@kGWWim-B{*eyh-J#jmcfByat6|l2qIi1k?j-LV&UFo#(1eZSjc$EiY^NGkaWJ3de`4!NGh|jb9nJr3|aRwrSf%ySnV-W"
    "#xU!OXu^(8dvk^rax<=Xcu!suPc<b8#oMFlc(+*JA2SWe{1`zEe^2Q=0hX&6>AQEP6Yhm+JPNSX!)Jesr_AG;IH;~%WA9%*XO5xA"
    "9@D895kxp<l;-|Y3ug|6W6IDk`uizvrWx57`B>t;iHutXSn6eg&&f5GQb+S}&Wt)5`?gYjU)T57<dzva?!s}dD1&X1HUUUC`BB_O"
    "5qy{g*yWgEjBs44W@#Rdd&@l4^wWfXKcy1wVn2@g`x@`UVCr>80rq-~?T$a&4RL$~n+4eKj~Hz3V+l!~h8NHqsYppE`BGFi3*c0v"
    "7T=_L^I6iIh)X2I;sIR2dPncgig1DnwhFL#o?a3K4#PJqD)T1}wyBFn+eXM7qTqKHM@+mRSU1VWL4pOoHmE3K#o_?VX_8rhr8p!D"
    "R+}j2D<aD~jBoCU>^s5wTzyB}p)%(*!2Uta+27eaT-!GS#2a_^h|?MT2-NHmSBcBtU%@i(n0ytq#?}O{m~0AP_|$O9+2{+O*&|%x"
    "H>P?NV80T^LQw_FWqd(!jg&OlCa$=gFZ5=QxFTR#@V$h7m4>2Y_K2&c?;rmfd&RV!3Rz2fJ`(#I%$d-3<T4HTiV#_n4&n1NQ3>CC"
    "uaCWwI>5v_`=aA&`(ehF9QVCX2F`3#8DgoMB@eLFL#iyma=8t$e;lru7F}tO(K`EpCp8&t8epkh^ng7+a>2VSz!HgAavVI7bv`B3"
    "X*muaZ=9Q&=XejtBxK9CpGX5d#C~Ps{ys~;{X{)i57?u|p1x-0Tm)FW1d#ZyQy<GcnJI#`;*#P08}02U&T{u-_itBHrvk_Nj*ho0"
    "B5hlaLm6P19Og6%$E9*Yig4V;8hQ`qKj=^tt`-*IY~L{sRbSt@c#Ruq=Kf85ED?j26^;Td?!t<LUPXev`NqsSz>-`M2Uy%hlGB&_"
    "*!#Ck7b;(`yEx;rzT+gsUNU?YjLThQzCKxFDKAzLV%J0&|I9!27eDSN_2FG^k0;wtXL6>V&WHxVzTRT86SrTXo`$h+YBfM2H*(a0"
    "<8sfaYE>6baEo_3=1Z;&i|^2$UlHN6Dm19)AE~m~saHgFw>UzIm6<a8nU9h*Cj=GsP=v!F53o#LW$Zf*YV3~-#Ca9_uQn7#oWaD$"
    "5@$aN710GzoY|~!uu5D>H~;J}j)<sJ7TU0jG46IV8l6AxDVOWwpPI!fp_PdO>#x;p`~GD6b^YthnrJ%j=iDyV;$1-=)A?GrqKG@x"
    "U*|Ppq{tl_%=Z4toT{Fe`l)&g?Im}#eer>)1RMJwzTuv__^Rw;gI8HMhr<8x4O~D^=j=1d9jWl70hUtxeP5-7IWCz46<~?fpe%Hf"
    ")L5#FiLVU5TXGGueI@PPlB<d5D@%gCV)iHtu+*y)U+BGCa<BD+bzU;z(NSRXza!KP!_VGXc=v%+X#F{pULD^gtg%z(*{1)Fsm5L~"
    "=A{32zQ)d(n)y-qz284QEZ#-TmR%HKn&m#0xPoO||4VO3hm6M+OQzC(9JFGrvD;@a8Eh3`sVolPAtR}A%mWbrS<rIIJpl154AfY>"
    "jjYT$53qRlNNu$HYGIAN*$j3E7-jw=+?xKcy9a8X`0DPG=@5~Iw{wj>Cc*((9Ac--;qMAEIcxgi2jgP>2kU@WFEpBi$J>`gQ*z;L"
    "U*i4aDd`0BzVRQ&qRBrykr*rD3iE3<?89!qj~|Gk`}fP$De-(J4!TkrETgw{uxlm|=5xi>sWhe`bjx5|PICHAts498l=<Eei@UPp"
    "pnI2KaY>Rzowed>v-ncz>XbAR%K$s0_$m#sOew;^?NDR!j9K9gZ;$?1aHR-+gX{W;=rt+M2k&OQ9!t3iB;UqQep3{&JKl(^pIjX$"
    "U;eLt5}6fQc=`l;&S2vJOFg9Wll@jdi8O;+*D8bWC9J|M+@l&xoxaYTsp>|4W^avU-kS%f{&r4fzr?<dR}Xs5bOQAy#_gQ6u!3=k"
    "{wB3m=<CwApXCOe+(PMR{vs=oV5%s<eq*w2eZSxB=j}05HN{sHZ;98?Mzn_G{;%hZTP9d!ybrtaKc@i}sG4Y2IQCIQN%=gAd|`h3"
    "*_2#BMohXWBH7hn+x2eF)Hn7MWexV>j&;Jl-iY;-@Q7p{w5F<U-t7$)f%T60j~P_}E%p_m|N6MSy~3kZBgr&xr+xp#=zd7gckj-!"
    "DB@!)AIsG^^)fc^pUiP>(_qU0i`VU}*~z=#@1HHHu6BM1_5Q^ViRB%eN^Uhzij*_|<IPI!&5OfEoF~ltKeC&DyPtlt&F}P&7l-;@"
    "je@;<^_)w4^E}Ct!?|F*qn@sE|DP|nk3TWk#K#irU*Er89QJ-X+rF4VcUc<LDsO>=1{-zZ#5#MtIz8vALwlm{e#+Dv%!AHEH5Shg"
    "G<%f#SgwFru+(!x7nO5e1=w36UDnUBzn^{vrJvua%A)Y-eCF@YdOI024X;z*?7jc}IetTl&fqzk1WQyfNPY9O#&WG!y?odE*_;qK"
    "qE32;==`NANCIaD`rA}v-%t!$23V>wvCoh-cFDYajDm4-eaYyt-X5KwaaCVDgU(=?ut@3e(HUWsMZudsNorb7hn$&t&}PffQ%0+|"
    "FBfAXRxWj^J?wlY&H*IS-ACb^;Gfp{49^NMC*9kT#VOGPA`cphiKhs!l@xjJ_!f8CD2K{#my55l#cD2kP-7Px!JYB-gc&7mP}nHS"
    "byD?|2=}Kg>fzSgNmC}#)JFwo6<K~>))p(#r^D{Appa2AThqx@PhD*8$1AF7piA~JaA3H~no&}Eh3Qu5P;;j5vlV)#K<mSEi!vMO"
    "lSudW$J6ag$+N8&1fOTK_`=@Q`_1}VvDGkI?89@eQH3`mo|A76GE;LSYRcIe)VI&IaF+A3K4rc!X?_7Z0&Y!MQDX|qWgRRwqR#M3"
    "ts4_@G;4zh3KIo|qhBMO8Cje93oZ)GC}o2}IZA|~8|&3Mb3zLb^=<d&DUL1u5jT=HxxGD+%M|WUWHi{k`4QYe7}+$HFWWyqK78X#"
    "`3N`F+j<W3daA?0T<6F8BB^%-I~5HI5&~`%sb>YzXO4b_(c86^D-~d&vUK#58L@*&+Muwb>b~N5$+ao0?{4dGXt56;ThYMF7DWhK"
    "w;IPc+@+8=2{SDgT7P#KYaLhxwYV$ad}h`sZGHh=AK5{-BNxCt<E9bD7f2f{n-tA2QmNxX`l=~rV#;U(V%GV1H_|%!{m1*0kGrQc"
    "w#T;-yecJ332sOSD=ht=Pj~;dzW?nbp>?E9_lgauRF_s%YNc-DR3yY~(O`+^(w3d1FDIi-*|CU@oPsJF6kS8ZW?HsbNN?2YUeC^U"
    "PiDjsD_ayM?hI2&7syLoXS3cyMN!&XG>Wz2nZa@^DHdwfViAp~vSZ1E6i5`<)j%{!^ZRx_;&MUGh(=~7rhd!g8;L|LX2W;AwX79F"
    "Emt&3RDo3NaxA}0Dp59qVCsi6)?(D4u$w)z^nX4jiuH{~4GNOmi5&&eH{>W~_V+PEuV!rh>T{V7Eh3T*7Mh`&X<Ek{nqjQ;(y^K_"
    "uZjkRjiTT3d3Supj8ZlzY?Rc}FJ@#r>Da!)_OK6+n7hXJio!i|iCc{YuzGUsnmy8*;SY<T*uK0wULyV?vu>HAKjrntvV+CeEpAbG"
    "FiSm1TF@I<w^(&=EyN9o`b<x&7T<<kO!oI{S;`opX@lDSamQ$1i4TPG5ZpQoWc?g7!Kwy=iO|B)pF>uEGbQ-jg{4*SYPoFa7Ivc`"
    "7lF*mt?i$mnCqq)<rB76_ONVMGl_abJLo2+g|DGe><&UkdghFJQz;r*t0K4JLK?{tYn3!8gb%GwSknVWy4i8}`?VnnnUGeP$g3`B"
    "K2|tL_zw~$ZdDNzRp{NSUYub<+s%J*$C%q$gMwxiyRTm2o;}x6q()tjt=+d-5#gK6IgYe~F|_+`wQnIqxNs+zuoGj~Ku2p7Lwjo1"
    "L99IJE6i7GQD2BBW2J}Yle(UjT0|GQ;M4|p#cv7SRSngqYA&=^W-P6I3(=QK58XRLUnxE4S{x}ynPRPsC2MEJ)fm^JD+YzhF1uFp"
    "q#cqK?%Qt}iLJk;rC%ZL%9I}AcC*4tzriCQhP9#w1>J^PK3Yq&LiCB!LuXK`d7Cr-=BCy(9x~f4r50<&naXwvY^uCcD!S}TFfO(T"
    "hWWL)D<p`_qP<x`i!4r$O6kQFd2(d44d30|pAUvP5?A?IE2%;g%PsvasCDR4o7$m>R8jAf)(b@(uqsvF+%f*KDAOb&gW7&N+n$}>"
    "KYhturg;O$4zgJUEeZ-L35lhDg^445u4RgU5`jMth3h<qnX?uM$)(cLoBE=JZ%v<rwLs3XW*d<-bxm0hhGw`maA+e^3&CA^k?Z1N"
    "P+IPT^6i^bR<^$Yg>T#rzB@v-P+?;?3Suk^y<LAyLvSf%ra0=aRjq?<wm-(ZKPKDb$?nA!5l2u<M}G&`G@`6Q(KkZnM!bMl(l+^$"
    "a;!&4@H&oiM}NnBkrg}QIp>()g+4tj#{YH)?=L2d4OO)$6ZFJFx-AM%gtHp^Y*O<u8y_^@IURH&rQQaWlTznUQ!e;{WF@Nx&gLV<"
    "qb?T9M~Yh%9wJvO-W0rLxT|PTkR++>D4-)TQ+3PK!evfz+@LV)vUK#21r%%I=<I6uctx;W)S|FiRhIt!9cKIJSA2l%%FKl-w1zF<"
    "nznD}wE!%1H|0t%ug;-WwZD%CTuk7pML{uKRme?gR%Y+w28G;!sakMKf6KYS<JgWxN6!VTU$-J|%+$G3-$J&7NxL0cdc5#s>Z;bf"
    "U5if!dDv)YwPqgcjY_qHOwm!se^oRn%nZzx9!w-IR8KRdK^gO;Y*1JbHg@!vn2nYwJ@OT%?xi_vO~p$jNkBt0bE4y+98q<~&X@AK"
    "iZT{b=d{=QmXO#nTe&!*V|?<0AW|&xb(QNQDX1?<)N+(N`so-^GD|f>OnpTndqH=~prp1*t&a`rMOEI8LYv;TZljaeB9PE+Wo|<)"
    "{0N;;bE36?A;boj{%=U#BJE-u*Nrx^k=CxY>c|vbx7j=Uep8ZRZqM{Tx8LiN_)^LK@00(k)iALHA<e2_e_wwb{{$<*nIWJGBw8a5"
    "{8?D$#9FY+`&qVBzLCKC$s364WS3)0e-35i+ZV43Q$B^@rKCY&I+Cui)UjmTEOCQEMzIMwTJcgB{K+HAFJxc7nEI1M{-kOzTD202"
    "h$WW(?V6dJxmHY_Nur{)T47q9656T4(Gz|ZTXtCMSd#vPSl>Z-SV(gic_SjPEh0z1pmHH}r#|dn{J<=f($Y^Sm<8m1{{l-n(~Dkf"
    "LPDq8{r>k)jBS!ODD10s2R}eJugpqM*$oj9&Rmv)K|!<9Q>oP*A^OPDBfjg{HA`KN!3^zKtyifuxTMdBN(>K+-36&d)!c=9>eO<n"
    "QDkbLSra=?BG)>0KF{Ti*!94DZG&`|E5t`?PL1I=t!D_VfNe(b{%-r{&j+3YsdxSA^w;fAhLdB9`U;+6I|>oRsa)srt5cYtQ%nC2"
    "GjsIRU!4+u58+8WD{wF3bmZuX09LGL*`Nk=Ip!irkspLoM&lUzDO}IgLuY=Fb_i?uz{6tKR@R~bQ_G4kE!zmu+tmgy6zh98B^DWB"
    "l{F|#oEovC1r?#Zdh^w$q#?5-WrM;FNUHR7-h1S_mRyhJ^)8(=pLej(PU+uQKbz;Pj9QX+u#j1*UIkO6krB~ZgTi*f&FyBxzgz5L"
    "u`}XONFGS$(k-+ABgE~MrN>f|>?Nhe5+MaXwe*WSj6PF(DT)Yjn%Q?#SCC0yC>s<uN@D5%*K<bl<P8dww}sM6^*@Lk9sR{?=Cx7W"
    "pt!S{xikaCBF;B8)s-Hv(xc_mzcY1mWHrp(zDxf*LJn(4&Y-X$Y2MP~g|LhR{Qik4`Stits=(pRrp>KqOX@+qnp*llC|)fZ6n0K!"
    "9c-~UB(P=5v<m&rhB1gN3iEiUBh%aH{%pLhrOmrBQWjPH$@kM4sHIot;+Cp$k7sy>k3Jw0t#4`S_AICWLyEZlaVLp%vk6y=r{?uc"
    "CtdT?(e~X5@l+-*9dJrJmvdVK%a*P~B$NrV3O)09RXbD(>YJ3Bt@XBH^DH(JP3iS?5fUw{I#|qfOj}e9c_`+Q6?WaWKQ6Y{KZd#;"
    "BsSyO*6D*5*)A9HdPGpELwzB<lg1=)C?-cOvi0>8%PUVs2MZ}Tanz!qv)#~d<f+eMy}cbvA&=>V2)-7U8<|QIQSMH(aY^$JJfz1;"
    "()_~z3u8D{PuYV%2<ZW%_Un)kzE)?m^hgSelS@QHDPc&5f~(aSRMnv9NKay44p=yp`Q%Q`+YR<aQ`zq`V$ztZm*ygG>Rm!bD0JP{"
    "^g$M;GSk!gn22yQ<$dpG<C^7&Ju=lp?q{^9G1%B*S^YS+ou_>)rm^LUqC?0c;>>Kd4komoiKGAa|6fX&A54)S<iD$eeircyn_T~g"
    "e+tt63+Sg{v9CoE?GLimYQ*JjIOqHfbupX#7_B18Jf=z;6lV1)kDU=kz$K~3jsn@1@-6!9Ga@BAx3xPJg+0wRqrCk{RCCB|;9ODI"
    "w-`3iI;6DBsXACF450dkqM#X;N>8jq<*Yt~!os(SrC;M2NKvjUV5+HNs45v*3swxM-xj_Y`Hwwf#Lyd0lcf*2`akw_wV?E=n4lIv"
    "kx}%ekfp~*iS68WvyaFqqeMq}-7nWZG>Wle>c#9QH2lZmb=KnJih@?4@aR3B`Hww3qrczI3jY>W!=z;4?Hg?O%a$IPl?G)kJv^(C"
    "2_8$nRIj}I5GvJgnRI-n2UpBAyWKvXZQsqH9Wj}XmL8s!mK+t-d*WMS^E{(Q31=evQsyl^vM*)U(&L<OOxNv;S}u(-9*$djVifZ&"
    "$5)*$;D<+vT6%niO<G2c>OZI+IK^??qM&^-X_1y5*_SwP>4|TVe-hQ})pKZ8CJoNg<NIQ~kW%pFn2~!X@}VebH_d%y>5)@xA|;ld"
    ";IY!8-W_2)X1@LOb$yB%nV&T%Y?P#>hh%=<(&OK5WVpCJKVUmzybzWimwU>StF!Hg4Khk%Jnxns=X_n^)vT|{51nG&O@qSDOWD#R"
    "r`X(ImLA_1^SEpKb=`Mm5Am3JT&gJS1}|EAgvZR2PD_v9#l{z1n}Hn<`JqupCac5J<2<I3#m6gg3L!j}dGx@nY$}z~6FQYaJ(+Ch"
    "8*E4NmLAfnqLv<?l}5O0)a4CvQZ#ODP?(OCwDi!oj9Pl)q{NDn!lTeF?C77JVf3Y?zc|8nFl*_dTfS=Pi8GaYMQ?HW5OqrB+EVhf"
    "N0MFI`GqzFqjziBVzpd8F>Z@hpX%^fu4%WSuQkToH^cOC;r;%}Q9pb$IJb5srL;sZDnBH1Y`c1ct?$HlGiKbZEj_%?zcF+YZQl`t"
    "-4`bvz$Sjl<HdTnIC)@g^R~RQBt}aufGc9Sk@uO9nDwUjf0p+z@A_p9hE}F*;kNVKyVr6;`%UaF4u7&HKs-C)lv{nGV^ENI)OW2)"
    "4_&@#OHY{3T3PsnGa_6KXfdP0{&R=*qN;@u({r_P&xz^T2751VBp?X+c8ttFc`1+B3Efx=lhyKSOt68bo*NXVQRgi^!Uj>+(i46v"
    "SDfqmi1?PcDFFsrMp;V_d0onup3teZIM=#UnC##Ut2b9IW8Z>0SklrHoSfR~RGgp6mV)YpCJ*Yyan;fjb90rm*3X%_m9Bo)9GaWn"
    "+DcEHvZSffg`JnEr6;_>BZ~^7?T2;OsHG=730h|2BkHZnJ$gd=Y2lBX?ezj1#Yn&T9cY8tPJ~KNaEm@!ob@AIgL<q!()%Ei9I_2P"
    "dSY&)_JI>Iw~>41G{gA6Z0Ye)V)vxS?1H>=rY32ekPW=neo1&9!2f(o!b=}66@)nn6HFeuGPKWxwCi9TBYBI$F0#C(M`l%czmJ;_"
    "`gr5|v{S|7pvyu<pVA|`wEkV`i9IzJ*=hqC)T7j+Cq!jo|LO9JXz7q8?s6b+R~UWT(i7T6(c~pUpWkFmJv+l0Qd<`*3L7P9=@D5}"
    "7A-vyJBV%K({ESM3Kt_wzaq3s8`(D~Xq3Ea=@ES|FI#%(+l#b{^hJ=37ki`p`@Xn*CU5Rd^m8@s>wEuxXq3`EF%?wrP0qg`h~~@O"
    "qO3vrEB5dE(tB!p&AGDl4}D8buhk_iJ@zeT1x$=}HSb56hfwA&{&o8aA4^t1qrhL6QV;=H0rk>bdSC_ABWmg4Z_zvxDL*}X^x&*A"
    "lPKBJBRrOSzmKo5IhDV@t^2*J2Ughf^Uo*S)tS7pe{hk@T1nQx^v8Zbg8^pNMN<^Uob4zKn?;K1cXl6G1Wf@F)cFRRTh`LULSSSr"
    "GC}n!j~rSz!#rh!Lgr?JL62)T_=Fr8tsHIXakeop(zj24h!2NAnQwXavTrI5qAH7ec7m^V)P&J{DLO-3szED*f>zt4b6a|x-$s!O"
    "@sEiwvgryp{YvYDUz9Ychrg)iQX_oCo&M~S86|B{&?x5Wk@SOJMU0`dFsd39BuI^MYUv3<YS#JXwEt{jQ1T?2PQXbXQyHPY6J_a$"
    "u~Lg#ePPB*Eb99ab3s&!68=Gy5S#2_=<zQy|5T$o58w~)Y}V4_qZl{Z_Vjh9Soy(G3YT0#DM&6+1ebD|T&i}gzDs;aCa7$@zUn7G"
    "44&4kL19wPqsRHpgdJ-XaUx0^;@o~ZGrsPd?&o+9#6*8n;y<5u`otgpki4ZQHnda}d9(|QT22|18*9y6b~@J0`q!5gAx@2BK~dOo"
    "s9Jh_LycZqqqgrU7A+bSwzE}BkI&6Ss3j%4*W-C`-Qos?tXpi?c|#~mrH#DTDEx|)bx=WSPz2ZM4FB3laew?=l%qpAPJ^gOQQQS#"
    "DspaDpZXr)L6tjIl!lEM_A7lL#DP&9K#0XR_i}xe_ks?CI)Ema)qnrQXvId7-=6hf$PU^dd4qxkg((DM>4|kPoAvb+H+v1re9_l$"
    "xNtU34D(Nq?>be~4<2C+*eN~1w3$WWPLI;{@_BsMuQN5YM{b7PI%u%(@g1(~nl*Pb?A6B~Tn&d>GM8^@zl+oKG`v`&W*bbOtXg_p"
    "XH!r9lSfjL25|&wr8%WXxK4fYN{`RVCg62ZwfQW4M81zrKco*2dEV?)rLZHS_GeW~4@pb!_X)-;Es7Jcny)p-4If!X&HSt-*kk5S"
    "v^i|^-IE0-D$AB0A4Ox7<7L10%8+2O`D0%W)#)A*FWSIn{Dl)`njJCz(l6mUbopx7u10~p6npeISHw}<e4SW%+iM(Od4qDzT<d#^"
    "xCokNs7rdklGwE%#ROoK?rq+A(1BCLP4iAhbI#h9pUAATq@^czHf|es5?6+1WYw422{yO1rN<*0nlCZ^Sxc4vE5(B@cRhWI!q1VG"
    "4K*n293?G1vD&FcF|J@$L`CD}#>x+6jtwcjDr4(|&?|C1z^htWNKv*T1a!qG4GQ9-svU)qCz;JvyJZyY++{a~6}}GhL($R`dt@65"
    "a<-&xYxD?@UYRqi4R}5v5l^#jc}q{MwjG62tuxn5h;ajI47Wygl0y#iTjbG0D^Ruc#O}m4V~vV>YZCbEBWK8{&R|g32})Xe;)~oU"
    "@VOJ|tu-jmH=TTpgC|Ja&nP`UH`RaMev+eypS#4h6j~AvWc8p*%4@wx<~~C2ms+msU1qV<eyiO<O`z&vF|8wOQMb||5}&QjIae%<"
    "vejlC3JMFBE;-7g_H^GFT2=i`i``RLY~aQpjXbO<`Jd$lM7_M<AKB**^}TuVdUyMIzel}v&kZ`ipx8GnZMiLVz%E`N`~{W&2Yx}6"
    "gu~eV^LH;e4xwzOx1wyVFk;QkiHn+Fkd%Y(jCN79r$EDA%n3?b?Da$*=DfJN9~1nk?}hCz{IwCGvF~Nj&@WW&n#=!Dyjry@zqj?s"
    "(0NpcmBlXZ&*v1k8@Hr4^ZJtQm3%pLJZ%p}1=b5*D=M2Mch*XqYiECCx|GhW7q1EBJZag+c4sFP+IG`-Z(eW5lm7dTp_!`|ZQ+Dn"
    "X?CsbVCj8NywO=+O}&jfP;qW>Xm87w^M1LcL8nC4!9o{7?2WjurvD&&M;$DdJQjCRgn^Lz*oW1d#G4_Z7PiM$%HMtcHWcJ7ZM95G"
    "KbuQ?qz8h+?F!h!Q-oUR#*$_jPjNHTD6ZO}u$w)8SaHo;dO|r&+Kz?<DpgcJQGYNep;A<*sL0_&$GD}3cr|P3aV1<$p2d-AyNL64"
    "*)}JGc-w2eMvPL~j$G&oN?Uru!=KsbFt<n8I_I{(QGL%cR=M?&?gMIDJ}5Mx=VCd&pE3?2y(Zq@;W={VOcl1L3vQ@Zu9Kqa>_W^?"
    "Uw>SWWqqLYt|jB^E8vb9CDJwkXs(XlaY|3f<jOWDc=Cw3p^65Dtw1{pBUkq~4>&Z6?Rl^CgoJc01fDS=6|Lm_q*gvx1Gkb{t3)Yb"
    "`BS#^#HlflCTej?<y^(KCVRhx!k{)aYEYaSSv94h&-YfbKFB}zY0r75#M!|$OuZQrVHX|cqq$`9{Pw6pF#)pbP*L9@HCUe!Srp@5"
    "s9Z@>gM~C$lfz)?O+yZ5th9rLtTU|(J=^p<Jr9nRH7JZX;+7u25J$Rt8^SeL+VXT#2DVqsbMTAu28Df5($W(ta2C~X7BV=uqCsJE"
    "OIvzenx(c#FBksP76Ua3Ox#NImYzs!w1sW)0H~Q;)u0}nTN2r4iBbghkFKryuLnk{QEG{ZJGVEtgQ(o*y(_9OlmGS53?n<k-9Jv4"
    "v0Bu_qoh`Y{k0lPn{aS$xlP;^)VrHby|4X{#73NdttK4>em{LyueDC>w4ZnSuLqbXiEPy}>-U~Ll3bkwEl3WoVP>=0`_A)&Q#JRs"
    "R96eL_zvx?Ey22)_M6NN@Sc|GP}E+nVCajIE*9H@qD8@5pe_1p18RHxk>T5_K|vf?>a)kAj+{KS=DF_at$2gC?>}mFsqV!5jw+*6"
    "dpDS9$VOe|ZR_;!M`ELaYa*rQ^X8|zUD$g?=Kpn{xo6nMY{%DeKh82FvZ|4X+N078io3GGaxCYX#QRu8O4th6ih_<(W$Akv2!nG="
    "8q~w1#O~eb`bgLS{Fd0g8&wqYEyhri=uFR8IQT8GjqfW88AUT*v@8ZAK#~T9iH@?RhmVP7{zxng+5Oa-mO_64i#0)&EeiS;t$n@e"
    "8`lTFCAB;wF)w7rgj?JL+ge22&Iu{4PYfQffAyZ{4^2-Wk37BWcs~v;ntfUM^sbXWv0qrF?sHyzxPLS07(|CZ#6BwQ8+rrRP5Z2}"
    "*VST3vZc04v(&G{&sq^TC}>Y3j~@Rb-5T>ulKG<8qLz=CFG?B|_C+2&t`fu}TM-&pwlka5En;eY3dv7px%#-__hW1`a1@2<vG#!^"
    "sCc;NtLJ*I35}>seIOy<iZ}owM^8&V*Q(L6(a#?|;G(dl3K2IlG%K?X*C)_Dl{UYBvYX60S^bA0Sp#8~D{oN{ePQV@Fb2@=`17gc"
    "&9ZvC9yi6}+Gb=QZ+24G4(rCbK5gs2bsZ8ox}i5439?Y%71<)g@|bRVu6ZvwHqn|Ae{FW(&+gBU4n?bnejzFSUl_0g5_##a^~|S-"
    "`Y|6ID2=r7nZ*Jdk&f(xwe9i;Bg4}Mg~@P_9>0}Ri|Tj485CkggTkC1m8(@gXYRhNL9wi8pZnF=^(liY8Wd|8X|AlrLN|^bYj4N5"
    "!>F=FA@n9UQs~13jKlYu{r&q_&lzhp@lcF4n%G=2#X?GTVskbWvNw_GFfa*#(1KJggk=enMc`wxNoFkyqPL89zxaR|<NEuLI1NOA"
    "c>sijk{zobMn5Q&a+~D8{XW@VVtS5>zV8!Ba=^_}jbMsac?r1$6Ki8CgxS!lMM2UsR(g}-IA-qO(V>^HLtJVu8v7FVK@~BvHm0SA"
    "b|*XZ()Qr)WbS!Ujq1fB2kl??;E~p@s{n{VbekFo!QS@G<FBvZArWL>FV1UIi?OrP28C@?(b5xcVLM7c&^hR-D;gB0Y`eFml(iMP"
    "!nw7U;$k$ony0>Ki-i`jvX4xA%@KwaFwMTJQMjWcj@*I>3gT7U(qef(1>IJ;rN<)+a=Yq^NsPD_-P-@6CS$A**O*|z#P9UfKf5Fj"
    "NbH`p7!<U>w%@^}^e-mdK87nMpT)aEa-hx3@vxZHZ$^Caqf<Wd;B}+or8Y&MT{5R5ZctEUr?O8|#d^gfl2zKGAigaueXR=-F8#7a"
    "L6JdoI*xB3&WUVG$K7<&fATXJuZ#~p`5d|d%cfBL7wmFz^u3ZkgK{-(P`q6Au+R+k@#cy!Nn&@Q8x$rX-6-df|0lNP<sUVTezrGv"
    "+Yd8F{*=uxJgj%c?mkj_V1`*fYMzMNRzz#Y9FAQc?7l~)2RSfycTJ5#PE*`GN;UKZpS!22%a70~_6^7<LjJ^#R}}@xE6vb;-Dy&P"
    "khfKeE;ix}WL+HkMYRHOAfIrM_p%Na3z(KIirA^bqMlu1=RLRdya&?mSB+iHiPb3GYP`RLb~$o0taVY7YeXpjszo@gsFyG{u7Yt1"
    "Ju`Q&V;XEPLu?3Jgya6>gt)=uxQm6y)$G9ri=M%_hr)R^^08xTckD}|2K#PLXPhB-MC5PKgfNy9XNor1|BtkHTW%vs(gt5;FL&<p"
    "e7K&gz38!-v3?**g0v`+`XzP~5_o`yY>^^aKV=0{pbD~|vVI=|c!y07_sEFML?-;}Eo*D5lKewNMtFF*d-y^B(i*ou`3w-knFJUM"
    "_I}Y#{~5r>iTAx6R@A8~-?znaoV2n39BZDp;y7&qyUnb7pT?p#7WmjWZ(%7Wwo?FP=<FAn{|od?shV>Kr5`c%nCjt|sj;bMjIe?2"
    "mUI|et1xI_Kh0Gv!5JAoO0ThmMFXpst8o|>9#?!HLB}@o$E~m$eV9hf8mLY|hCy$G$A|itwZxz2`TFw_V#7u)tSZi=XpgA#$R%x*"
    "p4$_Tf2iuz0pbMndEjv~0fJAW#`+LeXA5L)luFYs+bDo@{2ken`aQruNn>q$8>()3sEwNX5(nMs=N$OhE#(omKMj}p0IFM=Vf(bV"
    "4b7zzx|Joi{6f<63#J;m>KEdkU-<Dt`wQ9jU*N)k+Bx_~k|O{CWh`xAPmh3mBnibr_u(4J<LmZ}(ub-0YRR_dzeBGujgMUb?`3o&"
    "cxUs^OF-kzBr0C8%W*dga!_^5d@Mazsn;sWQy;rNdj#IOe73Ckjq;wbM`tMzC%<6qK0p#WEa1>1_GkcsNZrIbNjxl|-gu_p)@m(-"
    "&YZ@$x?8wtK=e0h(zu}{idBCLr<srKmH{91NtP|F>Px-5Nl<`I?P1?utzIsGRq{8qj>QFx5$|Iw3uy71%B+sVHcHJ!+-J&S@49_F"
    "2R}CQunQ^}t{04@x5)cHf!imO(C8XV$@r>OirOe3=Gj}NgT2b2My`+C#{%x1sJX%idw{c-TvFaDy&rX(ZV&Ek+`#JHXi*yr%sFXz"
    "El8od1~^%QMry3yC{Aqc${IVr)d`ujjRL+jYhZr>;W6A`rN%0a(}wV86rfI&4eaCyF{PVWO$Jb63o_KGAHZo1ea=5RB6q0%1-}x)"
    "p5C?ka-$9B^KYDMP+RkFjY?Jfd<AH0o-c@l!+~JYENNkpWA0-Q0Dmm0TTuh6f8R``i=2<`mXsencV!C>VB?^HJw+s&e@EXutxx8p"
    "TI($)&we4vHabVH+R(>hx=`kcxZiI#ACY%Jf0yr;-8wdd+?D#+&Eyz35rwx+ChgP~<x^kT{<ZtZ5;Bcr@3DZeZ!R>pt?yYCltM^0"
    "u6RbNS1B#MYkGb}1skWAnENPcvIj@qt0$280%Sg=fQ^R*AiH9J{%4Q^8ThA(L*)Tk9XGHi3xumP9}94GrKtOI@B0W))JXz({QUh8"
    "P*muC@wWK;0#JQ38;!%*$|^x#RT}Eb;x|BzjGK28Cn@ONQ*l%HFdV>U4J@Vx<PGfN5WyBc7BE`l=ABq!_0FQWc_;qZgC1xacOvIO"
    "0NBXKQig*5eu<mXqfT%D;7J><S3+W2U(tg@{3(@<Yxr~oO+GBs798;8Bn>v(%&vf2HO^XCKpG@Io0;qbK!SOD{pWnMzr9%N;47QA"
    "Vn0XguO@Bt?In<y=G_|Wmv_{H;Y1Z49C>Di0|K76+=I`7e8brGc=E8|5i8no?2MExIKri=k6nLy%{h;|-n0Dged>1W9-3|9Z_^X@"
    "nBvJI(?)89l;4ROSbdeGSSkkiSe2cdbWp&TCLVUYy8Zy@)j`<6E=Gt$z+d6s0^LKJjQ`b~9-?>ZdMW|E&|RFVLSmxEolZc#7cOaB"
    "F@(KcAQwbq!hnjK*bJH)+idmT>+OlNHcG#|L1RQ!xs0fx^AHLOqxEzi!p;D9O`4`n?BFANCe64l{fs0q60s8oX&bI_l_yCX1uTxg"
    "9W%gHm^5!3&h7!QMFabAhG2bWIETCqq33_&rgB3Yn%D+3HT~B+)dBJE7e)cc*<aOrAQX_!rN1)EZeM^Q=YTIW-yD!12JlWq4eb0D"
    "ctI`;9}7fb(JkX+FQ7-0*o%pkj3<qpr-h1IK;*bJvB(_}rOgQ=FD7x=#3Jv8QPRKyHe=LOmIw=om&jLmD(nmhEr|2xxcVSH(&57v"
    "7Wv-9#{$M$)YJjS-`2A!g7t3Xw?6@qNUzu)cK;lU$c>t}Km|wKAYobhSm^Ox+PGLO;1!ITw-2|u)Zae-ap0^y0Gl+h&~b>GSdIQq"
    "Bc^Q>U?oKjEE35X$Bk72Vn{OE8`{GHrf6ncDtmB*F`8J&>5+Pu{{9{2OKdRJH(;CS^7WQ$GFs^qe#zJg+E``$zb_;WP?v5HwNZdw"
    "mN&4U50Ltz{%4MrMJl48gVK-an>mv)=3(#x224{_<gFz07-?I((!o^<8`#BxZk3`o3JBEkRv4|36(lX})`n0+8n5qX&=<Jy?;Xw#"
    "*84WSmrBASdE!x?x3CCD6%FhdQ7wF1hFY?Y5o@c7ojvXF>G?K@X>5UfW7)t$HJQCgREnh^odbS3|4uhpfFFE&pEIEKxt9Lz%(=|^"
    "+qsB+EbuNsd+LAhxH4geE$FE5=Q&osut!DOMrqvdUi`M809h0^u*i!;!!)a~`YV{EZq&l6q>z8IICmR}nDs_H9$^`*z9D%$p^$ID"
    "&+m^5mL-gvs_e-v@a`Ek^{bOx;x_=BG_W%yy0STED4H}18{<OZ2Mra%B;8|PLH~~9oPB+uh`-Ax3m~vRYTi=@i-bn|Tf9(JrHh)k"
    "2BY-+>}xNkQUPG&_?ydB4)m6w7otg6B!waJjs3IB_1in-Huso$Mgb2ye5YyX(*uF-<gjXtrIi1%uM;u~kZffGi}+nL|LJG8SkDd+"
    "6D(?BRhE?R4PcaBQ}TV_vn9YkiL@!Hv6v?5-&r#(S14@o(sDCB8{)mVDF7>p4b=zsJ;R?5p=gcB=fKa0K#Xo8<^3)83UDlwbrASi"
    "D8Dc8&vk`Gf@~w-hN`g8Yq&q>YN0-V7-&U3XvcZ$c0PHY>#AXUSx$liR?NE}FXmVhna|195r7;EQS<OJT<;u<n&;QRk*_WqSfn~%"
    ">eck%ewRRIw;zqey)qRyd&8Ttt;6P^JWm_gO7%i(bNLqKwr<FSkMfPt6=ktK{=eo%Hb}fg+|>83N0`USmmc$9fTWF@60gEe5jU@Y"
    "emNmRFSUI8_u&S3?;xq=eec6J$lV(G>uj*PZenp81*DZl4eV!?b`fQH8wE6W2^!e{`3=csPJAps?hh58&l~gfJ9KXi&uG}`M3029"
    "`nE}hg(4Pw-@?N;?0GJ1%$dsF06q<W_ZRCkpnpN^@5O>DLIZs6%LIc}ah<QTEsz@2Nuy@e`o{#aSQGD5Qn`S)m+N0gfCBH8=-C`D"
    "S654VURN|Mi@gW#&1AZI3)DP}yr3q=YVJfoR7_9+|Cc@%ON{mSftdd#Qd20+8raz*(lE<kr8B@=MQ>FN?CS5A$eGO>*zbrYA7>3L"
    "l;Z8Z{%j^UtN8?(v%g1+)!&u(IHjuuna>-G^~*cJ{~0vKg*-5E(i|76yW2Pm3#Es_&%qRw-i8gDv!#}NVEvycZv28izAFo(G;3j1"
    "GC57!D8Pr~3C2nwYkfFb8wGd?eC*i{4^<q7o&{>U{f;zs`y+pbi~?Soyfrzw0a_W-xOoc;K1mmCIOf?XTW}}~#y8>wuIiK#v{8WY"
    "_paB|5foFA<npnU?DN^USm!rL^;D5*bjjLIrj!rzaK!(~T}_cPv$^I6b(L~6`%_43Kl`!<)Ul6k%+lwPs#-qDH>UqUhfbkEaidc9"
    "vjMMl{L0MUIkasndj=S*>K$e_?(^O1?G>Wkr8P=3O3W{M6^D;zW?LW8n?>$5Q+&J9ff2?ieIQbizGwh7rNY@jI6ng(SW}w<d@;u="
    "!Sa$`>pJa{$!tD{&2vo@F`sBQkTr=s>;z!LQ=_PqG9T5^OC^ieDE3HUz>HC(mLtrT)hIOVCo_Rnq|85ldtUCXF3wgD2kY1K&Cv*H"
    "F&6QU03HBZ($b)eUaeYE{!HY_IF-CM(!lir-jS5Vsf07V8eH!bO+{{lV4vrE&-e50Tf={CAFD`hd?pnct}dW$)gF4Wh19cso{zf4"
    "2l`M+8F1J<b&$Vq@A7|b-{m5UZDV4CqB2mA4I%Si+m<DZ>lqr<d+n#0;gTBI6@&f51rAkRE6vm0j|v@Xn|pb1p0SVJJr?(>X8ND!"
    "EqS#Sm4@=1O03oF?bu7teY%-m`7MDQvFC>+)pk%aVJIPO&kw)4&a~dKY=IP0Bk=-QZDUq%EoeNz@SGA`akZ%=sbct?syRB;&NU}`"
    "qizYka`ke{d({N??*O3@$+WvxLmw)qzCD>m-S7UQPzq@ZJs@7V-~D+v5Uy{v(^5h>Eb57By6)ujvgQXuk@?oFuhoyr9qM4O72MK`"
    "3Ov;N5j8*Bg(BXIA|FLfPxNcTBG<#}zOL|4>f5BWvYLUF1W+ty^?`BZwwv?Kw`$9SpXs(<DeBE^y>Tlo%QVPdH`TNLt@N-O`pj)T"
    "JEdEJ{r|N^FXgkq{CUxJP4q5EUUM~}c8)^y!kHI*uJ!kq!6rU-$5N!V+`ge$dgUm#LJO6{Rm*K!c3C|m4fOYs(TAxh_fk7nX50N#"
    "C~9!oaRdzlvl<8p$()Bf>_+tUGKOtZPf1}P4@qO3JRxG)!|F%mzY>($bPbcR;4-My{^fcyQK3wXfuP<^Ru_BPO;4@RW2|22rIL~?"
    "!0U0V)o<@qldz2fMhqI*i!(%%i5=Dy;6k=CZDDm^nzT{Crg&`7iK`g|I$qUlIEKj`8*H_O2iAvMLJ0PFZ+$XH_SEsi`sDU`u4DKl"
    "YNG%F;(h7)+4|ue;DjV=Vf7L(O>2qg;JS}Z+bCc}$Ar}{YY%B$wo$-_rVZ@%?(5!+*g@$>j2qtwT;i!U!D{UF2*3u7aTT)NW4vmh"
    "(<9yPJHb_%y^ukX#12a?wb^3x`kj*7D|qS&lg-Efcl~nFM!9D!BV$X;Hq#e~bd741jyW?&4>)`*s*}&&gUTrtC$;SH<%t_))UO^?"
    "*Yy1zy?2Z*5ix6)=<%+)qqR#^So71MR7be5nk_?qyih@S0yRXxwruYkpw<j2tg6E(=-3wa=vnMeQ!9+@r+t0e+FGL5eP`XLjMXZ)"
    "g;WZ9egsrv<2OhwYN6kPEcSqUS7Bj|i^n<O3<<0pt5C;FoqH#6^uQ=)0hi-e=gof0v|#$yLrE{ad1w%NKzWc^0cNS~tHP+=bIYt2"
    "$MgX6q%bP5Jg}sUKRxphko|AVcB)`68?c;j(yw35Xxtwo`uERQgItt3xZZq@?V3DjIXug)hh#a|^9G^JSgV&)LRGfg$*pw7+UeZR"
    "<%|ec&y9&ieR%@7(VP^Edeod35}_ux%AwRE)Qp%pEbqn6QxMA)#wfCd_jM@4mV$bJtTHHU(@a6#En7XN`%#HQ&8Mw;4*jUep{Pdj"
    "tqK)+-=)49$jz9$Pup6WU})nKHz;Y3$4469U0fC|)PUZY#vb#VcD;ZmU|+jxtYYyU8v~xP+^&P#KrpXDyz<9-ft*GXxK60a7}({2"
    "XLz%osC66L-G)&+cb4eGz|rp%YqrOb&;#DfOi-O7Y=fM@JA0!&ym8^^fju?+_Ie2z#kTTuh1!~CH3T$wIs<hd6+3#pbIb(KR4Dx;"
    "3*E@PO$McxNJh2GYoJPVh*L+e|0okwxqAJx+m~(dNhPgOy2q5#(d#en!kmk@SNe<FG_Z<m)b7(4ifdQs0bVs<w0{W%W7w+fa!muS"
    "8;hDufU!*ba)WwO-A5)>s-oX~ywZC=IM9@8IqKd1wS=@N%?qiqPZJM?C|8+P=NJo^7*UM^BvNMeD+cOiU}ojB0ZRWJ%{=)$GD_)N"
    "$gEbtDAj7jLa#n4neEXgAw9seSHvjIJ9uWBSqnX2!jyt~e@txOX|p@%7DxrFcEe`Yg-fU(W8ki56NY06fY%&@supBC9ndW^`yfJ;"
    "dd)4g8tHozV*|xC*@z>-0y3>&6fxmWhk0rB5RRq*Vy-eq@uUClm@76qm|m|foAgFPoqj-!Sv%H39cyGOax)6xRl9oKw!A~U8p-PE"
    "^$;@_&+xV01(8}$;OhMWo9C+Vj9NpmsNMADF<t0^a2H+&wQ(&gaIAl)GgbhOO6~Pjp>*#u=CJc39Cypz51DC6BB<YA>$jCV9h<g~"
    "_lP)>rC5D`L}th$<rwf{*&ryoHS|oL*h}s3!|F;G62^!9@Pl4NknzQ4)Zb^T|M?9FH3{r#GC&o_vd?7pw4UDVmc~S%I(k5VFiU+s"
    "?k1-X#(&0)0=CsQ(deQ~HL%eZ2kiFXNwdq>2f(FMYmC=3P2fakYf=fl-T}f__Vp#^nJ*k_H)BL$$WDWbUTt4zwz+L3DD>+_ueYp*"
    "{eHWC^+Ip9@Ov@8P6Eb`X$x*qhyh|>5ac~nZ%PE#`ePtzfcFSCYhXViZgW!#Qn1yIblSWQeQcPvu)EpDK3)h4a}>DUBth}@Zao=o"
    "P7Z(x^F77C@CRkv=@&U<RhF^yd#diZQy5k#K8ZdG*jA61e(V8H{50FNfz>-b0;{wO_J!VDO6~h5V@bN6Pmu48J?s;Z!xBhLqhMdX"
    "0F3cKl2QdbGJW(EJ1gdZj{;Vy^s#`#8At?Fjim%|0PC&NXx6RBF^KiPcUu|uL5}jUlXL2Us}U4Q*+u~dlsoBA2p>71^00-)o{9o%"
    "TKd1B`QF%{^Bm*hB=E5iM}_`uD<K1MW0?C`RdPWfxqcRPMFzFz#Dzf{r5dY)0#?;q87lXRoV7S=VAW|&hJQRxI5SB-s*5#lqX3EI"
    "?c;0#g%fjkY>Qo1s>{$5XZ?i1^q)sqT2SF(&nIMWLIJvgHP}19pm9w%WUonihDQ(L_Ae;LO+Ag2Y8!sNgR*1H1CTeaaiJh{&RbYO"
    "rbSU33!DOPwYkcc>eh(bC}2c)<4{!xO|(^DoijcPkT9`_-BMX-aJGeq{YHL2{k|j}EN}+h3EE6e*;x1t7F&Nobq2k&usMF$Ejuvu"
    "#LuqI-+yghjgTh*^SyUdc9;M>9NH1@7Sw}4<AgL-xrAQ-1i+HNLQTfNYB2v8l&p!yBN3zyrFgd@2){lX2<4}LK2*h5WJMdLce4bE"
    "!>T?ick~b6C^cB+oN>zz%*~X=W7Ov3Z{)_*jAhCdHc-H7WDYwWJwN=?jp){7GrJ=nl<M`+?wZ>4GtNxrkfq)!WP-GLO_u8i$c?}="
    "Ty9>SAtEcPQM%w0ORtWoF|H>&H}&hhiNi5R@{i@}{0e!a3>XEd#IaQrIlvDPp=PJ%_f*JQ{kTa$_C+udcrFP9r4E{+#pmN(q0ZHe"
    "QAzB=e%fM;FroRbhlA=5^;%rQGc+j3CZ!Qg!k}Q0`#P&N4G+6pfYiDlqo9Z5TIaOb-D8DrJ&~{|p5a9AC(mlJV^F*2R#?B5p$Fbr"
    "BYRVPAL-vjjH}!%#dnhvgfK}~hZ%oY<sW5r1nGAm|0u6rN#7UG%Ow_O&t47#M0`Q~Q43&~YaP{~!1uMl0lz=4UM^G&%y+aw0Y{9L"
    "F-ED5iCYTfi^3YUIXO_(!>OH|yaM_+YgT0!zX31Z^mbn|3eX=)`&||4^Hi56Q#g7cNGxF#n9d+$ZH{k|81<k=Ay0CKD}I2*2iQH!"
    "4-?RZQrcav%!k<mdAAKL>IrznXA=xUCH6f2c%g})CVJ*}rUwEHc;!cW=eE(N7&U&LYt<VQ9b`D_=ZNyi^insnx4!}I4pFYziRpo$"
    "FSEHnPoL*|t&;e?IyR@_)DZnxtg}_XKbNbob6r$}Kvv@sy*#QQQ3C>Stf{H^@{am1?6j0id2|zcAdseD6u_~GZPQ!{irE6t<P*6T"
    "1*kbt+{2pbfzWGSy18D_BL8a6sHe*CH)8OP3cmoVLMrfuBEmM814Z;pBx)rT6d1x(3QE6OHn@czVLt-ZpA0Z|Kz-6~CKe(Cfj}2-"
    "gj%7dOCXCmjBAu8C_S@v6&wVxvNH$Vd6sQuB%z0lCR;tA#_kN@kpi=ojqvggiD)earS==-RvV-gSGA>JB%ApndLl>eZf*xNIs<%A"
    "HvfW9YAI^YGLJRm=xD{+FC9HlbI*>VFo$#Nb{2ZIy~#l%WVZaS2yUSOPF}HlOmF0J>lNx8Djb^DC|$I6?C1e^QzEEq>QuOyC`-i1"
    "SbD8HwGof&(UQheMGhy99<Zl)wU?W}y+f*>nVo%eu$m#6q1@`CgW^A_jA%`0rO9Z><#)VB#@(mn+}hd|rN+;n+Yk$(2P9s`D4;f}"
    "t-rT^^MP_eMo`9m;(&k-!^0i1GOV>3DU6fX@B%u;2^UeXP}gcrDY2T5LFufj*wO0)%S#!B0-Sc<xrx=ciGGPxPc;k9*;{()XM!cx"
    "W9pCgJfDzf2@Fq?25tNc`k<!78y5*`HFJ&}))XPpbC;Y@53ABlB8QUfZw-pMOHeneypPCAZy%-i&_+oE3*;lXB{ku`Gh|TjGvAK@"
    "<*hpGS?XbrmGv%y(p#eI%WkL0LFP$XSS(t=MvOOpK@&5>h7Y6uSgt-#v5K;hHA(mv*a@$xWE*?qRtHTVfnT>oXDm7KjsUKRy>*77"
    "g^4RXZmgu)PTeo6rJsf9$MVG2>gS03qMG57ppDY6OyE{k%x9HYh}tN9L|oxcC^by<IwNn1h>Pq6B=q-~B#FZYRv$G=`<{4M(<4u_"
    "GNJc%Z-1&Pz1Rx3HA+>YB(mzOMXAbJMApb+)V{7hb0l$G4HRJ1xZ?oJH|`-N*tse?I<o#TAEn=SpJ$FIsv@qD1mrYOdM*u<26i^p"
    "ePeUP3*>4}n%}5bAS3IvVeH8*5YZP|wV$!4M;de0tgXj;XGRIpNJZ~97Ze~By&ah?D853qBWW82tZLw4fvPO#*6=vtd_tL$ieeX$"
    "KjO9)MT57$w<8yGppLXH11?zV=zXM<bsh?F{h2TI_T}MQH6joj?3pB+gQL~;7*X%rSlwOVr26J>?=;0947cZP6tE*s2O!t<SKaNC"
    "Wo;A?P2|oOwaLSD=CpxT8+vKozngDZz{O!u`)7c=%vMw;)IVOUyy&b^Gd<uBF}tvTPR}d)FJdP^g<1kqF-&AEGRhPZIAmuy)9cqQ"
    "u%l=KXl)5}q1V6L@=dgVPLj6zf5n|^V$AXyHP8`ts0;<4HU5R!p+?`%Ym1oYsZSe^EK1F{xy_Uz)b$<~fK(5M_@nq~n^a232g`o)"
    "gLiskhhBAAwVMFFjZB!jVaUl?TPwp<w>EqQRr|51kH|shrsor&*r{P-`$hja09e-~_%I4MXx#F6azwGgdK8-slL_^egW@sR9c_R>"
    "vEur&W}xOsG6ym}U<&c{e(A5g+{Q373V9#2D7_*YThzxxtZD?SXCD`<&wD@trQF)fpGH)r4Om7q+^0LBw+lrh$2AH#Vk|T&)ccX<"
    "_;ZsBp$E$N1dP(=!tgd#^yBIC{7f@9vu=e$0Xe_9heB#Tgw~Q`?BgAYYt7ds9Td<kFRQVb%R00cT#W^Qu>-zGa-agYBb2P6u{1-;"
    "P-~!ose0@42atkc#*G{n3EDJQcHpp(4>q*^9Kiy>un21)IVu$?rDizynNYd8B=m+G%_@~xY8tE0OBlr7FWjqq9aKoet*t!m0sG?3"
    "xl-OvfdXz~$1!$d0{KpK-7{G$U?6ol*+U%29<~y*zrP-GAct0Osp+9cu4!W|z;#J4t={6CzScyB8`Ie1z4Hmh^FvQFwoIA)!aqn>"
    ">v+CsqX2W#AMt?xe+oVOI*H`xPy?SFC+%MVByj9wcP>;EdhB#PQhE48>p%BVK;oOXK0j_(cMD);61O#!Lw$aU6ogMaENtx>W_D{u"
    "4|eJTxrQt3%pp`}CE){-rxuhoN|%Y8J9>Qp6?<Gi0q<pL9jrBdfi*AVSIY{u09G&I*K<K3?Qd-FA;EGx8%_Qf|G7a)Az2NIUxgUO"
    "`Hw1;`#RYL4ax+!3u=0$3DPiS_EU#C9{~v<h4qj#77BB<4UcN9V*R~&0;7~QYIFQ<_2!)_MJSfJLDDadWQL%ZxTsMavWRpcaU%jn"
    "ifV^j4FpcBoN@izM3y>!Ce(6FPd^$PFiUFG>g6|}uzc#RjK!)vw3b^4#ievre%+u(Q7tb;*tXesHx`z7mAbQ|Dtc_YGzz_5eGTNh"
    "facw{Fe#%{h2lB<cnSohnPiQ)Myb*m*-&D7z-o|D$XL)PL9oMZdb#>?p(>HVE<~o+lyqP_i0Oe|S}dzCfjhl^<CtEl0^@CKIiUwQ"
    "EwZR5pf$Fe+mkA2KXjuYq1U`SSJi4`jcYlo&;XIlEZ*EJKw-1}hSt-C9%Tfq`LyGaDebOTTr-C<&C3A)aOg&q1aOUrV1_p+;~qgg"
    "(kzY`%P&5f2=l;0>2B5BmVpw~u7jW3JZ_;!)Ti8*Agi&8UUhEQ5S5-$6QJ^cWOIv-fgCFn#+GeGt>0Xb@~lWY$m%2xDB35pPg)g9"
    "UoXAZek;`c7D)i)8P3J|poyR7u*n(%q~jUA>tq4Bh{cP3ij?;+?E456KR-b79T;^)w%BsMdjEPyjHPMBP|;UEh3s#}D6IP-E6EjV"
    "0wt=4i~^f*nRPh3S$|w0Z!wXe76&SC0LR`iJy03aj56CJ8)_htr}j?FjC)p-;1+uHdQFB`xPw}sAJVm=5fq_yR?HT_D|TvM%q!IF"
    "V5m!rZFowZKrha)+*`gP4G=+PTT$zWZ>#H>GGi;|gZ~+D0_1fJxj_M~f$O9a1JqR{NF2RBwUg!T=hu4Kp4ZX5)j+d7-P|%q52$VY"
    "MTda0=hop0i#K2n`Fy30<VhSopvlLA(pTxRosJo$a>tcc*J8;0US$Z|S}}~0Y<d+caVR8DHnZLL1goqFRMt#;#T9`7$69H1SBu>p"
    "Dwev%-%O^|-t_f5VDID<UvcKF%7#tt)6Zwb%t`IbYzIZ9t45c*ZEYv4uAqW`a&K0s*%e|a6%Mu7)0-_c&me1Ib&b{18U<9liX4ZN"
    "(`JOoBD?zp<d87UJOj5f)UHMOb*x=5ig#9pa(gHHu0nYWqFVXb(d$<)ar;H7AEzI5V}%ZNa-fO3Hr!}d?|ft;k+9dXm@BI=c3GJr"
    "=jbn_h5H4`<9qz3uh3{Lg}n6(q;FI=;QR)7=8H@JM=IU}79sSo-xtsK3nVz-eg68@Z1wwVcmYH27e0MhjmG+y0uzc5IJoKI4#=_G"
    "!yYeb<328sb@OIkU4NhE@Z)UhP2gWEoX+7u{0k3@_1OhdV7Y8zRf(&y{c5h6@ZM<P753p9$*zh0&+8FMjMM&3;z7{*9cel*@I4Y5"
    "58ryL^mpOh5lI7&w!kF^Tmuic!6i~|H$2-0r>FU`ZuHW+QqMo=Up-90WFz@ao)H;Sn)Cs-CAkrRCZUOypNf;!eph2$JCv?^j7JaD"
    "aE=)T7tG{iVt~3Anb6S#nH}b%{&Ar9$)t6xHRo^vmZSNrFTViiCk66FjMC>BrM5zHwMtMgt%&1<E7UdAVAQPq*O{I%@;V!iQY}VE"
    "TiZfVzrO}%$VQVv=~z8udeBxiC;b|G{zzEIW>j?*PF^EN*c*`|PZl~aSyZE-AWunaV&MLzK1e37!+ozuT4}?7&h*zRgT<gihXP*K"
    "m=#A<z6>Z6oe9cX;)s!Jv8NvZZ(eCFvTLAmaB3Uu8Wd7Hf@8g??iu3U<+C>bRar(zi}t)msTvBf%wc+<xTQfooas|?vidd0G=KoE"
    "u*|-qG7u_z$ZsFqazgL@OJq1rq14<KmnH>LlipQFOjY!HA4{FD@$gNb=9UL;&Gkt}W-KGweoV1cGUnJHx2ksYu|2#$&-De^O*uH)"
    "Q)0Z?61m6eM&7(R$0`*VKY(Oj1BI{Yuc*D_;Rjve>)g=;EyB$g{p}s_hG<JZ5(`1S8_WSTPRJ>uEo3!H=h=3nAo*Wr^(M!w{Yy$8"
    "08{%D<6+xOD&ytb>iUBzp!6EiIwA+3AFU3NSXtwTWGvkd)mMWafXHOB^Dj`Jsq2H)-P7s{$;=9P^{6)%5Z`ELZc;Wzx^m4)0|MNG"
    "cC0DTn>aS{kc2u}0=H+B3F`A5A}uWn3GxYzUACFr=<j!P5)%(~vpG^1`OHN(V64<X+$p7PIb}g{l>ikgbtrZBv9OFC%JjP&dd$sh"
    "31jFv9zZoWw}vWuIpa6b+eDJO{jH@FvROWSLG2+l&g7gIaG_6YrDe|&4}}EnCvu517SO<xT5g*d7^u{_u$BSpnmihm`$iQj@+Dr;"
    "f4M+P%w;tS31|rg^&RQgAQE*!5vK|vO!{yvA62azrh&^5AfPG~HYy!GpywNwFg?`3^5$s`L^v>Hl<J);vD-8qVcv|4=eDE;uZ+#<"
    "7|7#bY0vo)P-8EXyd%J!j8Rx+lIekyX!h&)NV|Z>7!i8?Bd_rfh=*CZbfLW(49fVC6wlu_P^w0$q8F?q$fAxZphblW8YoSt!cdGy"
    "L0unEH)_42!VJ&YA1}1?WCg&Wq@RUqp1DI!FQGQXQSRo+kzmNa=Pj)68{MjE@08HqeLhOR7knQvRyCGK4^*D9E2&rqQw=6|^m-9j"
    "^VR7GL~}@MlrGvfar8iDu{~w#ZUwn*Pe%HuK5QVVrN^yS9>%Go2b>ai6n!x<Tk4bgi(NynPN|?CkV-hLX3T&JFu5&$*hSH;qzfNS"
    "O}euAkvk2;$7RHE%g^(@?g##7AH$~+SHG-KU5lU(WyWHZ$th5d6-T^r&-3wWf1w>Ki-LktA6ggRe{Nleirxg93B7WZC=5;5?elz6"
    "sW+R+x5{>C9smFAIsS1Hv48t{zNL*w?`l-@G|%_X54YXy$X-+wu^uIE=UuBo^hU66byE+Hk_xI>cdmbw+|lb-Amt@BZ|<6%HE)r$"
    "1wZz5oKQM?Jtr8C5Y>F>MAP;1Ky@PWyhiPw8=auU(d$oZEEDKfxf$ebJGc2S<rmRdfrt9%cyqX1T{Sur{pZ%$g9>Ogb_S}rw1Pxs"
    "1EOD$EOx+Zmpi3m2bP5k#aQeMU}a3xlNzY{z{Gu^Zb1r1uRl-;AKN)KE>W&SVK0vFkKID4Ln|+b_i;TtP<>GxI(q$;VV+1RJawTM"
    "g|3*`(E}@B){XM_)mLX|ud~Hs_4_Swof+Ma6o5{kNbgul#6_Q|{8zIe?e=v@>^d;L{#rMwQWdJzdaqxI<&IvzZpL;dlv+`#E?Ktt"
    "o*(BVmbs1NE?GpVJaMRpU;3+-#3l<s#;TP8?kOgy>KoO&Oo{}Hcg8NqRODpmF3^Zs1GP8=Mr6Tju~gU}SRWr-EzxMJ$8~V6+zM07"
    ";mHD7tI)&V=oYGIK=izqmmYA@wWNmTnK*th4P5S3Qw<#_kjYRf%saWA`m%Xz^8OgmU`_3U8mQ7?2o*O_P2;!s(~6*h(%;vS<8vx>"
    "<~^zWXXi=94CJlG-Ll&xWoX9>Z$bW8c6~mB*tmiH3~)=}$sBrw-M`dGxiEH8j(`fC#LTmU(w}{gKPg12lc7JvY-#Lajm*(V^1_{?"
    "t^;{+J2D^GjUE{kGL1o7nHv2I>o$>#5F)d6GHPof=s|4Rz#?LbD~t)Yu3iY-1>Ur`MZWd&1MyPS!V*X6?-BY1Z*(bXh0KA@UF!b="
    "rAR+4HlL={*zxV-di1mz&3olc>79j>+ip$8!Sn9T{DkrjR^LauBkytb=}{|+wU;x?u#E!Fg2!Fe9yPsE+efsmLIt(0v&N91NQxF#"
    "H=?&PCWHoIq`Za28L4dlf@U|9&bX@GjM^w*Hya}=#`1(Vr3GCeV|n{{-L84nKVs5G0n*IlIsoN3N8BB65S^iPpGm=NkQ^u-+icCO"
    "9MX$e6fF0s4!{Ey4bU4b##A)xTp14Ep8%7Ym7EIosMt+1u`@@n9L2QFU{p71anPJE83pWqVQ=jUrBTuIh||M~{(27>h0Xt;dz6{@"
    "um{Z0_BIl%UZ$BUpp2q7ag!TJ>si_CZ!fERP5V=Y^)K;H=~Z_EW)2AHne0n6z)ArFzM6S}fshO@tTMpZPRiAG8D3a(gHcKuPAikQ"
    "Q2@tAK2|Z7;~zkJ8<V6m&jATsh!c4A@(kl}^X_26sP47<RY?hRE*Pa+huqSCJOt)uT(}(iqMchMC5(+MsK*c8V5-6Mo_biy1KJu@"
    "J2-k$|HA6^5^zT4a@YlXfJiDD*TcRaZQeX0<7PFM486`1`OsCErw#1&2$2|p!$K0HnseaR88aVpc?T5i@r0xbz#*Z-p4<YbrW!X3"
    "T3FSs7w2shz!inVR@TSt7xJavDnWJxjq6S>CS!AX>#4E3*C+7iIbW_{-mN|#?!G>V?Y->)rWe(y&1AZIJ5^0Gi#^m?tDWn16e(l8"
    "_1}OeOZyz(Es)#$Xe(l80r<@-l!^OYy}hD`6~LotQ2UqbH)q4X#L&F;toDBb+6%3-VTOY}l_x(J<xuE>V2pxM!24Y+FN}oxdWSqf"
    "$Be?BtyxUzyx-=vRMvsolL3lKVNp+zd!HXN7znVOsaa8>06$wU`d+nDfVGv&lUWzltxDAUG{8r`;*d^N?LpfisZq88hZY;<7F$i`"
    ")pY25W%e?vi1oosv6!xef-X(tSTOG+Bfw1N%gdm2FR-bj2kf0tP><h;wYb7wb%{J2@qbc~!<%<(+X5C%3H<EtucP3lh<^|W_@On)"
    "7zHSkrM-eH)T<ZBJG&jLQ}}UU{n>?1DCC%MwGBqC=QpeO2SeOWUnIPtH$cpq$AY@na#RvHRI6S1_MNThqtMX<VT7{URGMDT?dDx|"
    "bv<64|J0tuK;kYKg+!8si~@`xI*(?jt`D9cej#Ert5LA?fjQ8_s!Uq*1|cYwJ1%ncfIE)oHq)#9MrSbc_WBZX#)`Iiw^+U2QV(Qs"
    "xRil_0$Gh_9zzNBMQd45C`*vmsMUPBIy%}NAV&c(ZY;<iF+oQS?2hA1W4Re3AvzhOp!Y}a=0JXLb<mnYnS=Sq67Y?fTHb=XQu`KS"
    "3C>yl@wC3UudY9e6VtrTuuV4yeOYYK&F9^0-`?Y&*_+y+R0o;$y7|4{uWqiAgi(+`Dq;nDeh<7aWcEDH?=f#Yd)q41Xol$I@?Ai1"
    "T_C}7gwh8f(X)%J#^zY7DwxP>!%Gk2Rzg;PWOd=_0q?6>y@y}jdK5!k!HU-RJqfYU=z;8(`M#&t8*@jm*8tgpQz_EphusG@mWa3&"
    "E8f*f-wDaABjx)7xY{yn*jA{?Sm$`jh5lSeZ#?!w4+M+yay@F|Rg7AmJ9^;t!JM_lZ>s3K!hSo`>$jd|Z-siVcu6niRZi#u7fQMn"
    "Rq5x|>Gl(L2B#_?NM}bg)jW3enrPc3arF96OHzx1bT(ObOpr3_$KLawdpcVqarA%+B%`R33qnaw5qjXViy2iNZQ!zt@)`vsGGx{r"
    "$3Q45lATwa`+(RQCSSnAYNU7M(d$2rm1Kk3n&aR5qM8YN&_e^@3g(S_(XGZm=wvYR|L3UNUwcrW%o$~TDF?c{$!zq`)78uAO7pUu"
    "%Qn#v*O!3LkSm#+h-Cy73JPJu&_pe=+JNXnd5u!(LQ&x8f&9T#P{&Kv14QQ01MUUhqbHSnFc$Zq(Ce)p*_|gUk*#^Mi9C8htC4R}"
    "-Rz}kDMWv<hh4i#Sp%_$xl&BI8mq`v2^>A3e%Mc|#DeBd=W?kppQx3RYF3$}2ZWU=^7-n8Npw>CHo3<2s~4F0#;pb`l;)78j-INY"
    "sq(@KM-O<1%<jJ$lM8E!=*C>8`_-62`!v$PxG2}Js1VtDHqr#3MqIdZbhi461iNwx)@qUUshycTClLzqa)&1An^4min13=BwV$x("
    "Bl0OJuDq!JG=``I7ei)L+6%ab_`5E<4X=lsczg{RluDoEYl!KA3xY?vBk#TH92rSMC9)T~b5uHd;6jN6)ogOwzb~<)*N-AAb`QLs"
    "(}|F=u(#$!#?q%<(C*Zz@l<zxXO12SV#x({isVPsV<Exwa*2<Y>r?ZLKGS88<&mIfOQZmTLA^Nu+=;OS+!E?~rgG76gO4`{s!*j&"
    "qA!FVxLYmi;~{2fbN>qlYOek)cl5yY%ynrRRw98YC8J0^)A*fOEHFLbN0qq&uLhY_<i=BdPJ!`@CXB+2dR{%s$vWt3aWWK0#xl8r"
    "Un2!2xHHT63@E>lNMRO6sS^5VptOcSF>=NS7&t8SCY6ZWr^YJ$jqcNsRAv4;q+&*5d2%0lyGgAL$TdPWB`-`hkBVNEo}XGRl<5Jr"
    "O;B7i8hKPoe4ws&O5T6~F*&6G)dhvj0`h|2X~Hbc0>+LWQ2xzd9lUEb_UdQU($NFoVvfUPq<Rxc#X~FfdXa7_%MnWRP?%d5WqLrP"
    "HY_(8>qCo;hFsJrokkrxdLVklj-uE018Z*@l+H(;J9;3F$nfXKL#pHnXnJO~D~n7Y+?7f`HKTMoeB$T<k!aR!`hx!I;6N4CoLZq>"
    "p{@@Qt5(LsH2*9R)aYENALc@@mm!(up9*z80(4!znx|umGSzsAS!bAzRmn%Oq;E6*=H<=m-I2<%%u;uH33%=3BF+V+ca;+-@E2WT"
    "#Wzwn9KZ~*Ri7%9(x8h2N3Yj-xhu!?5-MdQ?w9G6DtD61tHjX*+axGpn-Xi_Pp?2ND-zTL;+Yqb@)LS%;H>BM@dyx-go<kv>hg+W"
    "53A9`b4#y|B{L4~q(<q)xLLj9$@7mF*nwhAzyNgvm5yFN3LmKB36}54dfoAa{F%@;Wmd*|Sl#_@<kImH{5r#gC%3@LQ{tgTVXq{a"
    "p!5ehm*@gQDR(*c=z(=883pMQT(1L5A0xg^1*HkLNu?@|&;wyDc9iQqT{3Cx=z-U(%%VoRccRGA1N8vSU!BbLnL$QW^198}qZ#ln"
    "P?j~SPBEajdrf{yEU}{oey@9IGg`sP;`#dpg@S*%(Y>UHjM5(^qZ{zzFMt@lQnIrNrIF{Q_0gRGk-Fwk7)CmMt*WY#N<|}~2lBGb"
    "YM*|1UL5KT6Zs;88pt|P`K2T8r?z!Q9<-{88jIa2)pD7z5Fe{rWVS>YrLxWC>j3qsu=dXB2cUFwVc)?|j{w<Q*su`l6?lNiAA>p@"
    "0RjApRmIO}I}oXr3g=W76I!%~-_vIcD)}-Qt$*HVY+E_t6^gpyjDUJCRA{L5u<8TFUImMy{vE&(4n6E6R$q&E#9*b&0(y>;sPPMm"
    "LnIH)HDnGXs>mf?V*z01fbWk%Y~H{kdK8y^tFf3imBbCKYHiB~L_g2c<Am!mbqWKpjssV}-vHd3N~tTs&hLQ&CaILJ5-i;~7YH_K"
    "U>~4yJtq9|qT5qra8Hv4R<oyN)_?%>bbL#ZNQh3(HLnCaf)=OrfHOd|N+t8!V(;k{K;w!GJk*<u%>-b3&QTKV{yB7H<Z;|$ff#!d"
    "+TNUDk?Yux-L@*#C5YQ7{k{YqBdK=8F*z3gM|yARV-?@!tp>1n?o3hdRLB5NEq0ECA6VW7P7__w!k@76L&|F0!m6C-R@$_hDD^wr"
    "OGgi^KXcS07yVvOZ;&;K99F*?9Pr7gA1|=W(ZjB;57)E3^{c5$ljJ{VAm31$<HLR-AEh}6N!~yyUct<#l{ISp=1hCQ6Sp8#6G;;o"
    "lS(;`1`6;jxs@b$^yCTIzSLolmsD}<<AN;Kvx}h$PV|}Hgs=Bhm4axhp+f;5=(w6n_dFaRh82&v#7a_#Dzc<_W1yN=B&gFPAiySf"
    "D4pS)J9;1>$E?HW(R%+<`*0lF2pL8#=laME<3Y-5tVTsANZ>&ZuZXX92BO4Lh>THCAu{uUZds7WtcX#YqbJp4R+Kq<AV`eo_8O|*"
    "5OK_Hb)%h~1MOW{wJ<1MS_;qY3OiP8X@0&kk#G8xnYc#j(uY$=uMe&Z+}y~-(-ko@k12Mzw?C1DKC|HGFDT1E6)qAxdO-R`f<l5!"
    "B&zd#w9*IPRxmdG3`+H4$ZxghBh!cIX``)K9VWK;xnSWo9C;ALB|EarFZB9pN0-P;T;P82{jsXO7oFDBp&rgjBmF;@fPah>hpheu"
    "yb8VB0(blC;q3fj_}Tetf4q794k?!9R?J+`kCniua(2Kk#O@b9f1q1teuKF9JUCQeF^;(WkziHt<DsK}SXBBI@Je2^v6>O(k=LL$"
    "Z+}u{fJ(gooKiboR`4Fa$-jIuEgMdIYB!O6y!)r9EXn6-{eu*?aoXReBnbL{kh=((-(kh_;ahJ}ss7)QPz25Iq=Uc1W|8K1;=$iJ"
    "SI>vUf;*U-|MkCt6A^n8Fy-8bs&Y}vQR(QXXFK}KkhBrDUt?E8R-;s`o6D?#U=m8Xiape&>MfftyTU_3mq;2X9@gw^eU(T%8-5E`"
    "-MsvRdEXE6A0j`<`{m8>&!>MO_brM#zp!&vW1ED_s3lU!CAN8R77I8}h||0UB!gwHn{C`i0V`bkSo#-ug*(5Xm~&+BZsH2f>ryq>"
    "G;cukk(^QBfN!Upzl~Ml4XNWCse`KD$Fyu<&!Je3(8vD&RqcqWybpOdQ3<g)s`XokQh$Ce#szyl(v6t5QNW?g92R=Wi*2;3#R6%$"
    "w6<jftNF|<Xh8I<>VM<4E~PHEF^4`1Sedec)hABYt_jB8E$Iko4qetk>1UfoJ{EW_if!m4WB*tJ{=Hb*8VYtk1^imE4N8>D@db3s"
    "YW-iZz(P47y&gWCLE@Av4Eu0^D?)eHs1(52Too!GW<HAQ0H}B=ZJ<6O*J9ygsr?FK<MRdQ{Q{L(xzGuRtc?QpCHJvFa0|`0F)qnK"
    ")ohD43Ycx#!0JorSJ*sgV4=GyY^;*%GxM+kL9&V>Pa9m1&UacUVc>t7c_>G#J%s+I+*8bkB3dsfym`JkTD@EVtezw-tg6I>|D_d5"
    ")6pQd5yFDHz~o+>`dEzR;;ey1gdR6;6D$;pK)e_ESm^qWd`{Ru*EZt|LLar6T_I@~Q46ct)4&&%)W~wA<Dbw+Q8a>ze~LB=SWi!6"
    "eLPfI=(K}z8>JsHh<q%aWz{#9Z4|(7-ue23brh`~eS$@NxslK3|5`^;f2}Gr|J4k@`d<w-Y$~IMs$j4x`#12oVtT2H1gIvO1Z@<+"
    "Oa3?BXp18e(Eq?2t)NcAHVV)Z8&g$<WDx6m^W@C05hA7YtPR&=6OZ>!Zh_p5*v5idES0$c=A1XM$B1lc&RHp|C4<{X0S2tc5+`#_"
    ";RQ2d*+v08@2}6C1^#Y^_jR@ttw$>?f;I}^0gvHNKR_Bn5PGv!XnKuZINPm}MxJ+ZJ=@zsAKM^Cp<hD9IVC>IVmGJI8hU$OT_2yI"
    "^XqZ-=POJ@OFaJM=VQQ682DJgkfGbwTPyJSPl{49_F}Hj5HWo2VJr0sDzNY0djCSRW;)SD`xjJaGisxN?`_U`hM3hs>0=f1^yC24"
    "vN^VO;RHLvEF)is0Y;2{6p)@4+l*#|r7+#^kH|gZ#@)RCO%<y^-<Y*gfQ)tfC~c;7I!O?^!$J+FU*4!p8_)MHDAfn%Z4|H_jsZ54"
    "DFyBV%u{&Sv(?`(5rL5SSU`vo)}QkN=%h)8YSO~$9<7|XrmjgkRNy`AZjRrPz|?57McGCHuM*xoD?UfCk<YQm)Iv`8HkY+gz-+w{"
    "Pi`;;&vWSz_HL<~Z5g#uz-(h5OPU5CxEiz7u5Fn#P*A-NF{>wlG{|foUo|~V^^DA>!d3JqI(l)5On?%~6z`M?YW5BYY!mg2P}m}f"
    "Zf1abh0t~w5#SG`|DD|61jOp4r?CT$r&viYaZVa6TD~L5JnUQ(@N7mb912ogGh4Bfv8tMQiK7SjzurMz16;X1Cy)Yf4W$Xtzbvqk"
    "w-<;ZT-Xw+|9GvJ%qAJ!@D)AtA!Y73aKb#C0d<+!we{smTjVYF=z(%Bh9AEC0vjTmow^)pDmIvPOB_8=|H`a(b%<Wx>FQs3^!gRx"
    "yYG6B0+TdV*XY2S&$%AKy%AIUDCuE!6<RVz0YyIoTd(_iq^e;USn*ZSPsY?`a<+K>=U5dp&oBN4sQoB%GUpBj)p`xA0m4|Q)@xv+"
    "=q*-JUMX<&K#@JOCS3UzC>WkFioDrC2_v&{)xlTak|q(O6x4&VcS+>vfxc8c%D2_;uaSaLIitw)43zk=D0LS+BWDspoxaw|8IK+)"
    "%EWv0P197u9QoYQ1NU0Nf3<#?BK%{<`Y{Du7KN=a{Bw$x4dKVQpXWd)?#xzuFesfyojH2FEo0nMn-|nM==sm(YGz`eG^LzO4BO__"
    "8Q|Tevz{>utc0A`DBV(c^gyZ+U8dxTLh5d@-;6y%)!l)#CZ{t+Mb{y_-bl;pfUF)ytH1B=SeMwM&~&Dh-60c?9;oYU)?sq?{P^wp"
    ";b8rFgoR5{@@ee-!Y{gxe@viqkzDdoeqlLZkIyMk)^v;oreQoM{3A4nmq;p8k<{4ATHm~Rq$tGWBV=^<3AB%2$M7;1ZvNzpo8Kbo"
    "R5JSN@0UpP>!3!dv>+4rMfBfCKp7>=V5-<Z+vHT}fnY5=%E@5jNh)C^o5{@zviKri;hXg*Bu_0)YZR=0r-8$&GTakK4`gTaY5=9N"
    "Oww*%qjW{rJ$j&5HLp3?CDuF$Za)476r!ZXGpOlu^%BYBGiC^*Fn>rXo;vaIYAO~Qe<0=)F2swnIlg_KPmqF00i&wF!m8bx&=CeA"
    "rhUmMtY^JZhBqe%s@SST!s&$`=x}6EvnxQmNF}hGLM)Dzs4^-`9_x9&NB36~_16KEQHg1PI}W0LRK{uD6iU=&zrSu-JwtEyNa*#W"
    "7^Z#x{;S(IZU|*O4^({e{3n1iQ882mvQxuka4hp(k9X@&BLHRG=7jpk!B(Swa7~DBpa0zJa?}vY7|ztXx9QmI-!C&m%7A;VABCe9"
    "DfeyKuqOVx<+A2=Fgx{gZ}l4Z7JfSHqA306`=j3gdT_f<H`q#CFZA0TNVD>nH`UNBS^d}Tvf3Q6P{wLio9S8nlBKTD19OW7)$uA1"
    "%`I{$9b*KB{<iB^AKEfwF0EcKH`9q~6mC_|^uP+3Q4aP@X$9p91TvOM)&thf__`&<uVXO{P0}bo0^Fw54Q^K8uqs9>9X%kO5=L!i"
    "Q{?O$)VrhA|9k^(A8r6$iL&t&k=5qA-jBN4#SjykLLY=W2T-zK6{@3r4&JIV7In_j&oCEMH+OjO4l-Qv{umKuB|p1tt(!Wy%e?Z("
    "B${?h_>wzanz|zIkS_`?>Ihgp7G)jO>ic1<uzBxnO@!p?t}--!Q=KoPX$U>=bw=RaJ*{q!5S014`Tgo*2JAAos(+Ylj;9Fsng;9N"
    "7pvcIk+U2ys%vl!o-Z@j;<xAd86u-HZXDl@U>uxb!p+&c)t?5hl|=eJ_taAEm)M!~3)@zyb#P6j6*#1eN^r}|C*;(Wwx{!$vJU^;"
    "Ll#py1!H1I8u-#!-3OyVU{(W>3%8U=JO+B9r>X<aaXUU%KW-ilVAVn?u+3rVcQ)_u5VbS$fusgBvpajfI*?-Z7HGQgY)^w7QmeAC"
    "@gu0J69!$lYVt+e08Xg{dV56Y(=%fQjTP20Mq_OeHkPr-MABcovKr@zN)||BlxfP0tbFQPIct_8>23WysD9Y?%77gahyWjL@vaXE"
    "VOjHKD`2?S`rx=krq>JY()Quq|B0+aByDOj$B6XdMJ&WpT0HEZb(41nFQd}+SJjWjaiRO?s|(~#iKJ_)miPD-cpq{r1ri&{Nww&O"
    "9w#lVilahVLvj;o=o352`B^tIf6y-{&2U@oeR~JufH$TGv@g4WfcBM135ZF%&|<$6Aa?Y?bzgE1P%<i2ER;HWJqvM=!{oeMGIvlA"
    "1vN_NYzZAbARM@#>7v`oW$=qi>6Hn%k1`3foW4LT)>019biDeESp9VeOn@IUsjO9@zK(Rt53j>zw;SxBScqzr?$YEHxWO!a4zN64"
    "B0HN&z~srCP^#-Mb@YIW5_8v~R{7ap-!EU~Ob?vyLb??FvDA6MQb!M5UR-8>iWo$h<g3mW*zQQ(bx_&ht9<r^jm6jH=c{gx>YzN~"
    "%FK6|mqSvS_9%W#brS`SUN5zzLgN`CwE_u>78GRHWHu|%U>AFSyR>eLv_9syb!^O!{5+s8Fh}$C+e_8Kks=RgTdU#qtku7VX<$n?"
    "pZWFW{A!I`i!}bVx9Ve@hjI4@cNVPsYkzU$T+;t{{Gd+b@_y?5F`}xa4WI@hnG|PR3%d=TV#fxEGbFQhvCg`+jQS^8G$4Ss96BJT"
    "EeAFu=4`mQ$Kb`9wtqqKu{JC1j7x&7X1`RPmLl;{+<2(pZx95YC?NXly&d$Kw*@_AtA`ddap!kyxX92lhG7e<^QCwbHZCk=>w^{+"
    "HnlwQ0y^$8TN~kQYqog5+0_{l(6SoX-D?}T_35ik-NQ(k_(Ct{t$_CayES(7z&m@m6-77Q=c)FcopTuf@p`p?2Y9ZycID;a>TZd6"
    "uHqV{QVwH}9`Ji-lDU8^resO{IMOmOD>h88m(|Aj-Msoh9T1p{PW!}B#<h=_Sf@)z9AAyNk4lzWn>Xi}d(hY{6$-PDIEeTCZ{+I+"
    "EMF5|czCuRog>Va)hM0C=g|YJmrA%ebaIVXhtl~u;0G`eQU?T<J(lQnz!)j(0Cmhm7-tfuj>N`r$dE*L|2g06&w*>GuyM<XYRAQX"
    "2{n6CY4u^@=r!`eyuJxN5PTwW&a1D8@(@Ke3b=x!(4kb$uFTP^zlduiGio#WMwReS=2!$&YIlk<0TF*@VnfY=vl-a1<eSyI39<!w"
    "jndutsiOyO{AeqRMAmGnyYb6VIC;_P4&QGJXF@+gf;@TGj*qZMWTO^R<%joUorVxPdO)(-@LlbdS43&ZDmsPlc8vP}=tE^vHkMGI"
    "5B$~sk8Sx8VHxsSrZO*`+~M9)sA6j@sL4~Spz(ifi<gdUr!5E3kCjJ#!0w~@_RmZL_QyWY$K9vT|L6&-uNIR#vN3A+H<E&!IeOg("
    "nz`{PljnzD+PT?oVvI7)77z6!#vIMd*lh;*(71t{ZCCjB@4koHW=Rb)Tk2zn$1*G}E7N^=?Ol^R<hPjT`B~TR+KVdej^EFr9gmGN"
    "@O)4GF`c*2Ff;$5emg?ro*MWm9p9R`>xX$aDyjD?YHok{)v`Lb?+aZfp`%x?754#r{ytiLxd4`h`OTnApv$G6-@>r0vAXYy9KCXs"
    "ic8J4NP%bSHIInjB+ml46iO?{D%8Q=ZhoM-m5yFHN_B#m6)RLn$LQT(np-BQW&^VR)15ea{R%`uU%ttpWaha&b`{7z-ZT6VJJjQr"
    "8lL~r>q1Ww&N{JJzj4x5Z~V~Yi@^QVa@-f&(EA~km`d{c7q~3O`t9XrG)I;qb-%FqjdHR8@#2lH;SG`%MGYBf)-X6>w`dg4aC(Gr"
    "i<>aE)TC*oEv)8yIqpJG(--D@)g#IocUaAc>?0D?`J_U%$MVu+iN4Gl^qtZNgL~m&FAvq{h}W}$-SJ(ymEnuMZrn@nD3ywCUR~+Q"
    "PcQLuD<3LUr!dH%7L-Xo+GwWJxIB75hRYYN_s>+CLm;_z8XbV>%gE8|*O|r0;*cC)J4cDF=y<#XZsgqRGZpIk0N}Jp#?s#`W_K)#"
    "q{M~Zz7s}$yxUB^=}`Y3#A(U)+T*v?*Iy!0)$g-CCzO9S(*NwPjr(^}i%Vdho3}qrkK-Zvlaz)0;QW@|L0TO$u)5ac9MCjktJnQ_"
    "q1Vt17Zs9^spq2D%J4tWx_t?UbV$|)|9omydf$GUNaytE^%|FnvwB|ctuCn3{qsM^tCv%X@7igt7xufBWAJFijMCeEMuJIZD`_|y"
    "3C8*-(*wGJ&7al#9|F5m2Gxo^*gn0$3b7iZo}n0$252MvwTdE#pa>Sxe9SkdEv)J@)5xKAag<q>+|fh+hrsF*OPv=euy)WA^8&?5"
    "T%+hYW47ovq3+#+!YZz;=j%T$EMQc1d6`s>t?f_;uUESTQ@|J(;j^5t{@AU^MM+rG1A?@a_OgU(RxaJnPNj8aFuneWnI4gq7^J)G"
    "{B-?lTuH@&`^(7QP!h~<7dly;I(p^jr*hNLg{Af)8s;elHCq5E&RHhZ6X0iyWE}wgJQvwgp;}oy{Z@cSuOEd|zdI<Ucbe{TqtsEm"
    "G(FR1(x0nBQ5KlJXLk>mNn=?Cs_2W{(QB^AqHy$pfs=ENf2(L`zkyRYdi_PrY0j^ofQvYiN|=nQz6-io1F3ajum^k3_X}X$u#MHN"
    "OzBY7R3X_OdtbV(hv^_Tbl4w=DNXz0u$T%#oKv*0s#W5oW=6qJ5~YvbIaX-i8CP%iR{#4+cfXk836&lTxhswHkWkknz4Df1i9=Z}"
    "eTP@as0|E(ygJ4gojR<>7oA33dNKp2%j)v=-=KScA@W89yfjh<gq%Wve?F^Ajv!-64G_qy&#&`@g1k?5hDwiLluGpvy}%?deVEoL"
    "omW3|^m>&tu%k44?QQ3TT-05m*IU_KN1{R<Bkvk@8JW*ls!KLX`)acca*nO&f(cu@rw?b^J*~!K@orF5C*%N8ed|g!4`%~`-$SDZ"
    "h5H4KE*E<v>UYhaj`hQCjxru#IfLDLCW9(LW-IDkX(cCdZ&agn++I3*fHyL!z@t}?a<P#arJ5V_1JmohWXypTYJ$AcOC1=x6Dj>)"
    "&ku!_FpS;F4~5m_nI2G_5~&WPUk&0t`7V+$07}N{me=l`A(_>-rqFz%TZcrd2|;hctkPF1tKP9teNkP5X!=5@_!(Y3`~Z0HtQT~3"
    "c%-r=3wxt6y?PX>`1EDD`Z-$dkM(AqIUR=gt`V<kVsGl}vEHaLsEkpdf@=2nniAZ)rAvCnOMMJ2P^CArM7mw5UZzT`gE77OG({|t"
    "et%6V1FCSllIa1*5qTI=K|P#l{O4TkclG;?O8csomrVes2Y59X)IVP9d{aWNe!61c6o31z-lJtWjo0}W&~R+XC8Kn=f9mJ~uaueF"
    "A4}El(C#OWUO$S-@#&(pF_ZLlnf$_+U&vi%c6mP4OQF!dBUdPubR}6AJ9@x6Gb=y81!OW=KxQ50^KKFK0f&4jV-ZUA=Ed@d>47(|"
    "f>D6yHnz6L{JvYpc}Ui=?3&-NN3($(=j{d#F-B3tktfbXQ0Hf=r+>b7nO^Ud=IXEW>d$v?mSLnw=#L@)m|4Jw1K?;Rk~m4n787Mr"
    "jnav-+|ldJI<9~FeL<y_E4y|7Zpd+zTQ!pDHKMP~9sT@Qt0_sp;3}l>U?uuGX+cB&gedB(SUC7T$iqES{Uy!&AirfWJzz8Df})nz"
    "NOW0hWs8SZIW1Wxe_zrW-+3r(ToW~dfowWnJq`|3J@6U&AA9s%0_;&KsIParJ&GJXa8yG^RU!`XmGL?ol*(5YyHNn!Dvm4)c`ivU"
    ">eC$%4`Ax0FbZ?#$5z$%uqv^iln$lH2jSY7LVrGj!eY5Oi^U?|?`ocT?y&smpm`r;TgIXkm!LO_{(9o4u?ltm0^uvW8b1JO7IE3|"
    "A1}I93kFs`%EKCk@m1|xsIY2JDM=fyV*PW}>N(Xbo!GC%^y<|}`6ahPosW>1;nG&Gz0g>BA(y#B;({V;v94b}bvt|wY1&-bY+Ie%"
    "LEn^&wVv%EH=`*I@bVYcA^<#=d5zL}EE7i$L_3(00<T^GKABQ{*A=Q;+j-DCnlY+d&Smh_hl0|_x~Cy$lv9=9N?n|ccMGvZuGDI7"
    "-K_9I@se5;^yV&ARV%#_d9=!Fl<p$V96jJVlR~&#v#0yV${h+2Uv~90;X{dKSEkn+p|RBFrCUIM1q6Zu9u||zgbF>>Bk+V|qqZ1J"
    "PdwKEA4>5P#=bx9RtOnPaY`MQU4NP#H;S>K_<B{K!Z52*v?KZ;<Wd5e9QNyz%B2}39%|Og?(cu_4caImj?SOwJ=qR};R;felIbDS"
    "sSN8{(E8XCLY3avO~+WmW9DJE6<HdTV4;syNEL4-_0qNey2%rufQ3<wQUxB=D?dX<iR}vLpV1SkgFz_0k0p^#F^t00(L_{wAFGnj"
    "LGDnR1TiZushmQkR-Ih{$?sv@!m48b;`WG0N-U2!Yt?J&eX`*qt4t55NxX)$^_vUCWm*afa<mrPQS>L3;OYi1ZGVGiRyl9gYwdl_"
    "k?Z&zco!zI!=qewOQ{cfxr-X5ax-!jxY0eO%<E(0S;MbTi^KKwW;LefJ3}&`24X(E#}cJusa+4GkObB=s8ITJX;QrHSn4NogR*1k"
    "_2E>4=*Sk^KL>Ok(U<PmpXMq}AdDQn>h>uez5Zb<mKEq0LLXWIkuCSs_(sL39=-m&%h6i`Hcn+su?F?#V0Ar1Oze<RfQvh}^7+lh"
    "^LzvZKh!Aw%SB;tt2Y;P233M9a`bu|hfCa7D7|G=y1A(WmP*TYOb^U06O`UnOSg6`sL5+Yze;M9?u$}K4{%*%QAfy`m9aMZC~KRJ"
    "u^vx>Afi;B%js=JE$d8}K`AJ;-e^K_GeI?rTKBEFoOGrKG?qe8ivxti8Fi-0r>MOdOb_f4_w_hi{SV|Gj0N@kEpnQ2Mpb`{@Po9#"
    "pb}C5O8S*_TZ0YlRGQn~D0{k)t<up0(m3wxz%uBiktQ9WZX>IQ={B~%iT)mp@_K(wj~Ml(W)?)+qX4gUsoN}l#DziCEoSbJ1jD#)"
    "69dOi*x+Y^PmXlXYL6bs(6p1(l#Q~%=Ryx?1;y5uH2qpZ+Sih1P?OL5TG9;OyuwJE_rD=GZ(5^tlD2U4dfCFo;VabN-XTXr<QP!a"
    "EVcJqh0=$P7k14L-s#J3m^C-6cQ9T38pD}i?Ctchy1<6Wp)}!?-0*Qi;n~V!fCd$|QNWsH4y!lDxigobknj=;0d=z_^;`dJSB)FQ"
    "4*TN;6xI@@d5typ>7ZRtt6F&UOU>gQp|Y}#QqM5qXH&+$y<A<7H*c4lgWJs;x^DiJx>(hGVsAbtw}AaiE8uv8-t3@s29{Ke)vR0L"
    "xPk^cnXm4EtnD!IK2yKor8nr0+tu9yIRfqjH?I#iFYYKoSo5W^8+0?9uihW1Btv9*qvC<ll3r0Y#YkC&n2cAq3nT_Ut5K?OYxYVp"
    "y<WZH*N4d%ctkF&mN=mbD#%!7%|9Ljg*pip2?{Ds$ex)>QQ1clbGThEsW%6Rk40t(+_|N_-#;z^osDilBR@ZlNFCKAznGwIp$7_<"
    "nw|Po3FpO*w>Ey8`!olRZFS_ifuKSC3li0=gBusf0q3rxj6!q3`L8TiF_t$&U=&{YxiZsSLTEnCu~d#g)&VPi%X;jmr}bw@|F?|="
    "XDZ1o=Yr{h^Bzh|LA`gqLa}yHp?<$rg%NTL!*mSAFeKb!l2QL0uYR8HdcQ7fdQ3yk>(vIzE16<Mi9=1t#1-hc+{bpRE6|i%pT-m~"
    "&}5^^YwT{jHTLEPyoT6ODn;nkcy*@yE?&t?!2484VM%IIsrHYV8$?i8q7Yk%6$(mXDwD0K^~+!6*3-Of=GI`GUI9)vI;7!N6i{zR"
    "nC%KP%J>qT-slT-hc@d?P(Kc^2NZsUGFW==t5g?FCQ;Hs0cK!SV@<nZUA8YPjXnxkRc}NnIH#x&zQgJ+l*FN+eDKO#WtSIYPi~>N"
    "atW03u)5i%4uuHD&{hwtv5K)WNB@8XY8JJ?zrmb=N$#TnrL>UxCyd?v?VY~j3aLpPhj2XUc0L_UMoYQhuIi$Rt?)lyf>k}uE}Yz|"
    "a_#8^#Z13?d4nj-QH@e5mK;#Q^uY6he2YFrC$ia{gi^<x8^cggfcz;WSxn9&;9f4dCo+&hnOS*tGS@uG8JBP5==D#Ttf-tUfV-xw"
    "$67#2k=!*EN^e%zD#z(-@cvB%1y!wK8E8<tx-q4r*XtzNc9d2psaBFZ$e(^7XNamUR^sRZxfclv%jU=hrLTlshku-YAah=I`;>hh"
    "z=u|z&BN0py(Bj|_2pI+kR8w5csA;`s~eIViToOt9nU;mp&oVF@vPx6J#g=sznbl-Z@0|R15!E_ls*ld_%;@lI%wbABQlo0)=g+T"
    "vry|d#bc|Hfr+CBWS}`6vqRvH%d9pyn*uIVdcxq<TTpbz{yE@IFB(8ZViW?@2dC8zr4H(Ou}3)<8ly6^QHa%#X#7i=RY92^U`XEd"
    "1=uc%*K?_AOHq3C%A65lkEOo6jPakCZ}~h@MGD1M998rWx|$5UtxOL@Z1SvLQy8-*Vv_@ynH~@kjJg66^kVC2sRn`yRYigV-u=nP"
    "Xi?O^K%Jz_riY+_JSmE^;<plm#e8vzjqb2mMaEg_=z(jL+n0}kH=tU@J)ck=3H{p#pY(I2AYN*7zRq<8@lqRCc@7rD3+>z{W1Xxk"
    "9X(L!+qNb@)fMMwb&=_T-I1o`R3aX@MoUHk(Z89b;ZrN~kB2HhKTC-(PjGXD-0~`80kt+_6jq8n3%8;Wwbrc6^$Wmd5!f5ydZcZU"
    "!0N&E2sAdi)A|jNz+PAhGyerTh|KxDACYYf+*t<oaHfiQr`0ZmUZ2fT$LUolO<T0wo-C#Znl6=$QaLNqFyc2{lMgQaXEmt2Xrq9F"
    "RH=_8PoQSRC~l+lBWB)+-$xXGt7)3Xj$c9PZ}8GXA(_tA-kI_mf~{;oqzFUAvXQaBUQuPpFE=XD!S6B#Nc<1Q{G^TzR&S@9$zt{S"
    "a5%#&DgqC31w@^tQddf_??>x5N16|e_!bb<vGQC<R9=nJq`roZMOTL(s{0zL^%S(QDnaBio1pZInY)8uX;!Nll9m;FU&^K7G_x&}"
    "HcHRlsW;-oX!Up9wU~RT#c%q~edbcgd@Kc4X}&Q}+9+U0oS32-RtHGpLzw$mC6kNy(nsk>ESe)ukxMG{<c6+EXxtc%nuX~PSLBO0"
    "gH<t)FE@USp=h@#O&eH6tdWsac^d`9e!C@IzkGVWpF=g!Vo#D|HQuXfhoOh9{-;XSjKZXi0_2ZdC@OgY1tP|QkJUav)A7t2KtTP7"
    "J>Wh4PsM&w8>Ly*tb@|eGi+k3+e9T}^EL{o9OdoBcnTHR^sjYJj{<JnxM*M@NgF2(?EF^8Jk1e*AS33bkJUQ?Ox{xydxGRld8!(g"
    "l2a#UGWOsdjjOtk!Zr#JfXxvRKICpGf}M<3Uq?tPgm=0>y{2*pdOq}wFUBJ8s^0g4EyBYrXkk&AFODz&7c?4j;+@&)CAL;^*uv^`"
    "&a{mJPP&IZ-h=o*3_R?~t*X{vYV!?!6fj}~OBDuylU_8i6QF;3;~qafs+3;+o`$~GVX!(WQMOS)>0@tSX3O>Dd`Cf&(i>}Lswryj"
    "#3F8^0D0n#czy;|+VmX=SP`n!CU;w`!a(-!{fBRm4kj^RH5N%c^qo1Bk56iYUf#B`$P2i)FTl;>ID9iXBfAxF>A2Za-!x>lkvH4T"
    "><%bVQooE>*x3|$CS(5j21J^X!!{EX=1NTjHG9&zQayUWnV$+u&!2g%!?aOaXMS!S=G8BJUm&yP^Y~3K`OU5+7IlG?-3SC#sfGI6"
    "KeIDbM`A~*+Xc;|k9op#qv)RSyx#{_o6q&P&B1{lW$)-ViegPa%~$V7nqY~j4j8EZYW53x{*L&sfV8;424?&?BAZ3^NK`s{y*A4("
    "njahu`?S&DTvUg-aM;D(^Wu<-d*368Y<!oQUs&y5QlsZ#KQ=i`N(VVQq9ahL6Vu9!JqN}uy&suR$*2ABuVm7hT)(XTDK6lQs11?B"
    "f}aqj9`<<o{8*i%1u}H(;13IZsY6q0(tR@3EhMReagIno&Q`9@-PwgNTUt5n^7>$i0mqs}@y$p*=6IloZ}Kmn=5({4_HtUn*=pN<"
    "!KjEMDz$WeGx!Tx?=MvHb28fT?eq&_-!JgW@0dd-Z>*bFs^}wAlP7ZY`p637X6d4UfL?R?ZeAS%3JImm2L?6aFqPG3q=thL0*qA!"
    "+{(&Ku!J4+FtK?BzGfQkWfYc6XfsBAtSbLKD;!GI(<gBBn%|E-dVMs4ap6|CHU&Aq8tcj`n$JJbS+%9;Z$hsRq+!OR$TXl}4j0zg"
    "{B4gCx8J<0JwFs{G2Uqrn-Tx^jw&YrK_F&ZC&yHx0VvFs2nw;FQ)Y?DS#=rFeRO_CJsQ4_SNr4YRz>uRvi==D)T_HCkULfhf8!hH"
    "Us&(YHh&xcE0=pFdZYZ#^aZsT@T*ZN%?g&ll@a<<n`>_r-O{1-@-RyT_4muw-P7vlsj4nVmbX!=Dlusr1;jnd*Qp|)5^+KbJ<upb"
    "7;-(mL!!7HN>#(TEQJ1KiNvYOnq&346N^Ibpd{ljx?R1SAg$-i8ig2}kwcxItsl;juPYoDaGTh9zDJT16XxDq%m6nDdW6E-Wb>(9"
    "P$aGDN-7<_{_KmKS*(xuR{M7<f2pY*wE6fOSjN+A)AUU9qH5@KM-SXV=5wY?Alsde70+$C9s%wDB9`+81=kz2ZO|F6tNLyh<oF%n"
    "va=102&D*%ifkQJp;wQ>4=99E#D_$-Ca2H?$x|_-w8>L!9WXthd&@dQR(WJX!Ym5O1+XcrjFk>Anv~?ca41OIx5;ikR<&!!xg;nJ"
    "ed2u=a2SO*)?c2GFG_2aZf>EY2a>0F1&**r-WCNoEh&bU_jjrdW-B8{4+u<iMow<@G4K`huvB@T?>#>>>Wltm+uQ<bm=int<|u#Z"
    "n_DPcN~q4$>R<Zj78NqLu0Ak0R>Y`o-q65Uv2jT~&tJ4!UiPg+WXv(4*MCvT>oD%-dh~u#AhqnC=O0?n*<0sE^yUN!y>f1)R3WZV"
    "-J*qqU&O0D>Dnm+D7I6m8bF7`2T}Z8TaqgWP%M)xb|o&->@4#t(*twM7}dR@dQrB8IyujmYE<=)kwVXlL(-{E+n2>(dPHkrYpT@1"
    "-K#-kne)C_bo04-2da3<+@XwG{r(zQ$qH-KMZq?eknNMKAjYr4kZz1hFUshOf>Mb-GqFlD>|7bWpJU%lpC9kKubI6l>t3T|g!74>"
    "F=GCr$8P{vRO}w*HOg0a|FTWp4I)WL5_;v_tfKP#I0ue=BqrhWa@;KlHn@7BpdQu2IhN>X%BSlnIYYvkFT@IUJlVZ^v`Kc9PF;@P"
    "Jqq0ywcPmqyy`~L^AEe7DUId*@oIG0o|xy5G|Oe02-C~mPe2-*oI9zRymPtiZ7%ex4=)|PeiMxaM=0cGiA-Vzp=JvNm0Hvjz?|GF"
    "_vH<+p>&tUjDmEbsN~i7re8yIm+?+5x|ZOe-o-OqwA#V<>s`5{*RLM8$$q)mygA=JN^G0XGre9|aclC|ORBuFbCgKhdkMXM#Y}$U"
    "YX6d6%+0Iuz&Ry-nA>6R>rPPh4>z{n-%_}*Pe9Qq#-GM0>diF2*W9WEj4}t@B@oQ#<c?nR`+NlUw^Uji+Dh(CU!gjEeh1`dn%brN"
    "e5aS~vAN?Ig_t>spdOI>lsnY#-|10iEVH=>d-_}0pfZaBbeP1r`U$lh>(?+cPI!Y_BC8QIs_SSSx+P;-4d-&%7R5a<+mLs`{{_v}"
    "W@oE8$i{5Uh5pTf&TK3kJs?_Tm&x0&`3e*CQdtD6hXX*PV*&ndqSe)nzC`poH6t|fFhURTkDZlXZ6M>w%<cWC`xHKSy_y-mKkl|M"
    "8oDe@WHPC9FK<-3y@|*o`v3V2QBER3buvANq-88~>$+!qFPcCC6(pf}=Y0`Ka(6cYx%U*X0?G7%btAh2sDhbWw-$<O7?Sbpf)WSW"
    "ss52A;IGI-L4AR|J+e66I!=S^VHW4`L${yZ5bK)P+tu{}py?G>3$0LZe<DV@Imp+SfXA%52u!*Gp%x23Q!+++g(5$#N`c88z22f>"
    "d*S*g;H-!xELpm)0|(ix`S0`syLvfYeYqL39EoG&njR6h1*7P_67ZcG)ZOCw&!4K}&%&AM0g-Oj?QRJOXItN_LXox%pkyr4I)Kv@"
    "32HV)tTS`DSK863N=1o{gHh;#FEXcZevkR9BSCe8lm^w6oKaM%Mr8@6jvknsS-0;CfFEoXtO}*_R9F8LLSNaBTIDm9w^T+^#PUnT"
    "^Xy}{y;Kg38?><+j*>I-{gE_Gm3o;vdcb>cPW|FHz*8LroVd*eE)Z8<QloTVlsS5U&kIIr%w)sonWG1^h+I&5H+61rv>$ujMB~95"
    "EfUn(B_j9Ccl~$)`RKTBnn67wD5D+y7-8NvzSn+^T1k$5rb=vL!i64Khn!K+t--NyRA>GgLWP1toX=9m$28OfOlhv3$8Gpj{^Zor"
    "Yfc}hiZean<t`beH9t9B@#P#dKLd+;IM(?aOGgjfWxT>q-L$wty^F_s(wbeI#>n(~11hm7h4V0|D?l<maO;^Bc=e)N>|)5R$0_gz"
    "wfa74#p3pI0;ez=6mq%?L8)beu`EhPb<0E#N^cpf8~Q$k;(Vo7<JD+PfwHQjmoQ{Anj^x8m;H40eS|y!@v_g<W<uiV0dEX1!VI{|"
    "tsj*F8kHeBe9W01c>5C+@OB*9YGwwd6Ti8mSMfmR==Ja5xka6ifar)cs!_YYrLMrw^r~;M->yG6A)ReTZKk?WIIouJfm34+^=Q^@"
    "_Btqbcm-yF(5`ztRglRMFhe;7_pMGq{l*c~lSz(v=93zw8->4R377zp?Ep1ef)A|nMcuZcgV(p&**Ab2Evy^aS17&O9NB`pZw@HW"
    "OaEP*RsH52h0<x<`*qnphUnSV#O$r#9JN{n^?Eb7EDY1@8C5>#Xf^+)I<QIX=z(ZG{+5eYf7{+*Cr%G%di~WS%yY3mAFHg$Kt>@?"
    "ugdDo9ld^5Tz-=amuXg*_kCNTv%w>fF$(i9g))|klViKWOt0tUdKAoFkaeRvhu;?}lY#5n)et~f*|GGVfw~;)cuFZwfY^xzb#eeG"
    "JX|Ys{B8AaGUTt0?4DAwyRmA~xG-ZyukrB2wsZp(wYx`nAYxQEgK1EE=Wn@F1(M}<AEAJOx~BcXJK*eOb-(p7U~6Z#cL1RjES=eF"
    "l<D<6#@#3;s%J#QlZm6(?@lCrw}Bfcw{xpZTF94M+8*Ef(1oB9iiMyaz5%vy9M&k+&C9Aa)9dY7S-k}rr%+T(X4`!0g;ivW|8pG)"
    ";Nq4R)s)JuxwzxN(d(b&*dZ`|L67n#hZ@*o>4QmF+rD8-eUIK>$R)5%eqpC2mCMtB&})PeS3zWYK=jFXk<3&*yxLaUKc>1!w$Rb*"
    "nKs>yBA3zpRucmd)*T|KZ!!|(mI<m`5`1v1(xT1*?=JhbD%6_`KyI)z$Dl|<{$r`~kQZee1$g5<tY$1eo=mTiY<x3T^mBzXr*618"
    "y;2>e!g}YJUjNn7lK86Cf4ujrh2O4};aD->x!YPu58Y65G_HV9`K%Tugwnn<X1078qf}ocE1-|cAWbipM!FDBhNW#LyT3rjvZ%uk"
    "h`UKp+Iagia`b>DZbzA@oLX`2(d+F*zJ|E4s_I)}M-NERQc!vqWp%~cM!GE&-Pf~UTCpG757cWrxqWKc*28y@2@~nAi+Jti$?0UF"
    "y4h)z)X@WT%cQR^k{lrh;K_nA_ccC$J{qSV^yY~{MSY!Tht`cN%5vvf)w<<<ooa_hDddaj!CEy+;pp|Fu!uOjp_o$DD5ay<ixjR8"
    "U!gS5=!F#y9E+lPkTQX8(z+B1Sd~Vx2l`;|u<jAYD2)$6=%>`#O?m6ZwwVZ{b}m|MnVIPUfs@$2s8hrnkoPr39Sjt&QAaBMiv1f*"
    "4@5lLPOr1QA>R>M*-ZIVmuy8IBeE7&wWqe1Ww%J_;7fXDdvrbl#%ydmdw!ZDhM4W%sLA=F<+dFX^?G1jk3uMI;y`SR&-*CA_ZvH`"
    "=Dw@UqQHF`l{3BG+l-d<o~Y*&GT4LqN4EA`9KeQbv@#Y-W1)R192Vm3xbDSy259N@rI|x*E7CqRV(ekJ^=Td4+0@7GexKr1{l{w{"
    "qBXJ##+N5m{AXm91g6((o@rF0OjSJ~;yns%cTV*UNOFwJFMoMb+7wX`IC>z4)1si~QNGc>{KD#Z$U6K2?!nC3=3jnoK3*Z;74a$o"
    "97{J;Sfe(t4uNU_+~dgtReZ=Yvx4Y?IwEdE@O1_xKxOu(CKM9Z!dk@FS*5aWt>!dT#e(Iz!D?j`p%RBuIe5KM^jsl5VP8O*8uFZX"
    "Jpyjh!ur(>iel%We4HqB*jF!r`?QesOo!bE{EcB0HL&`9FKk>TW0m_}*hT=1(ikB88hbrbdYq(9*!5^LyF$#Ol>7N&@{PG`{)^UJ"
    ";Sb~jdO{CK(WI|+#h^hQ_qB%@<b2z3L0`wl*4$&1%8M8Ujvjc4lg1Mif2E&W6k60h^894mG)%@i>6AEneE?ozn>$R7hU_B>>yq76"
    "<>Lf(+oNw#m||S76%t06)-5f*JpDg^#U8<k<FXnJ=<-G2q4f7vUM+eVrVeZB#J9^81J_Gj|CBOPK28G<vcM|61*wmPvT(x4!+J%v"
    "Rb>NW4|}kO>6`V*sIWR~&-QLIkn5kro&(#Y>zgRT`{%<aDNaL2|K?zIf#hBUZo6rq*%iX)rNcs2VD*hj(89u{6q2O<3mT7tG-3WG"
    "=0c@eqrRD>-1-Z;0PUcSRiQ#3weuU3*p0H8OxLr;=Jh*ZYf|@tTrO@0yJmq;Us;wrl7MSrrBQ$ABJ$_~!(D{1D%v8hJKTN)qAhY8"
    "ExQ;)fub=#iC2GhasT}5l}cxfq?Hh0E9BNM_2a1esMYyTU4%u}farCZ+_rZ4@dEKe<sRx0^FndEHo@xeXu2_rGODrlT}f?-9*+1w"
    "`QAi+Fx32@O4Etmn$%5-^vjZZOFGbpVc-|y!foZh5(h-JBi+`pV5dGU-xtUnV(%AB-VEsAlu%jzg-;(S{pflR;I6t=6v0vdecr<A"
    "?xxJ4wsnOX+Vs@1Utd?K!K36&cw1Mfp`3=;HanU<={{4she7IbC|%BOLG_s3rJ=(<egN`gA{$h~*yVWj^*6xb8s;_DbP1cQD)HFn"
    "U=9TY7c{Wcz+{dDHrnQ3tQ7-3&d6pzSS)3bXq<wPRpeSgK!c4MaHIfg5PKW+$5QKkj~xR82b`AIeJQ!qkk1Sg$HSPaOyjz(sSFAr"
    "$eOgfuz~&kW|uaY`1I@jyB*J@Md0WmF&o)*5D%-%-15F?I_@jIKQwL<Z2bit4`gjDa6BEmQtS`nYKr`?zB~k+VUZNtci4$8>D-g^"
    "*ds<{O>7TKFA_lU;K+yXWQo|DDz_^cW?HVqDc$)hE$jV=(wJV&{HA<cfr)M2=mAY1MXw*=_DmEW@#i^J_Ejx@>F5C;Va6zJA#IkQ"
    "Ot0VENO}g++%y+rk~n(Jw{ssSrUx>Rr2k>Jjp`tZ`_uuY!Hp+7;U;pRuPoz6aQfOpW-RUwGzG%Y$lIDqBe?S`Dld0F`M*e7&FGq}"
    "L=T{aOEalsK;q=`5W^^))tWnc;E5_0l$L#srI&_Yx4RD%de?Ne0!CvR4F6QM+KL!O^HWJV{8Q^w{fqy<N5%}@@q>z*=TYJM@vY`Z"
    "6gM@!9B9cmXwJE1uhwMq`iNT(13q8dc?~E)N+{dq?F~}-Fs@NZ=Be}xJ5!lbg~ZnpJre#JbEC|UNbM$iNinGDi2M<%e22i%>(x!8"
    "&2Od?;6;q?t)fP$oPCLOK_W@2ihe8|y`Bf8chV6cdE>gP(Gm8NSnwC!KF>#hn3euSghDJX^Ify6Zdbv<(^u9g<yd7RD^Jy@JFD^E"
    "J*Yet&mf^X_3{3@XNE;0Q3s6jx#+*QaS_qS9=&dEr7f9DsLq+~MTK(Gsq0Y3c<V)_lCkwX|Il)^Z~daY5KT+yy&wF)pMTPH|82);"
    "+(x5|Ce2|Oo!ivG3f;}C=^Zl==hO3iLJdE5ePL;<d<wmipK{5Uqh3cHEw2|<NO_Cr`5F1qxhEWe%^X&_8j(a!Q=g<xU8ljXGhA}N"
    "&~s#U#<+UL^TV%dCADWPkP=0V+Rc%rG(Yb4aN16vR(GPz%Df5OY>q}$3u*d7IYT2m3hx)TxV;Ck88_7Nv8KVZ{uhe6XI1qJM!y+w"
    ";SbFu^JY?+lHZLn^yZ!Z7xJ`d{Q~*mKVJdA5Qp_Itp0wsx<J;!SS^D6{bu#^VD<HGvp)xZA@F`dp?VJdRKjA>{8VM-Z;sDU#>iv0"
    "tyDAUZUKBqR66XNgNmg$Z<p)SoAt-VzxFvroVg#YA4Wh%jXn0D^R;N7P2YiGj+OTnJr5Lvb9VeppZtF=S2s)OMC6gTiJkEAAz<$9"
    "-RBSMPjh(pBX7Yk<`pMHzfk11*A)N4<zcJ6XrC}-M~I-dz3L1J5Rd2kf(QoSX_|ZRZ_nQ!kp*|lwK-d?Zk{%;4>m9E02y9{bx%HI"
    "&Z&n&HYlaIDTn>_iW<6jcEx{hvnwi8U{{ICjJ`kCYX}BgxW0pkc0sdE+?TE=6H2#J%r>-w$e{pjA#vDk?)HJT<tRxXyIVWARi_2D"
    ">+1}|d-T;1v*oZr%X7zLTQgFIxW(#DHCFXSski>y9O^^dQWQRR_gGob*VS^!?g}jG)eClSi(~uYTi-HfMcfCG0xPGzTacAuAC}$f"
    "zCV7;FHo3od%~6VLGp@!=bD}q2PW^%(PRwBnR+iKW9TdxeK>4kby{@fP>PEqtj_{+QHF_?W?!BV<tnRDln7^z9wO?a8jdYyHFTP{"
    "uv?>4dVe987yiaCD3&+Ry*V4NIxy!rc35z>fz@QXtzQO3cTuCrnf3V)(Gq2IH?z9|acTsPVeHDv*#8L#9F`sx>gyA-YekLPy<fS+"
    "j|ja|<VNzyQ%#^-jd#d|=S#Mlb~9dYyF<ep#iwTvfL}|Z7cNV2uJ<!kRy>zjtx(;n9KD;BNo%g>?-$*el-{vo>yxS!$cH`s3`4eY"
    "DyyWKi?#i}3nU+2==GixKFEt{H!Nsq9av<U#=xysK-)Pmv+89H0S<_5Lj1>4@1==YtQiz_j%mII_pKr4MmA6YM->jc*zztqh%IaE"
    "`sJM-YrGtZhb1K(Sf#+t+0=;qiSTFcW3^mb25l6;38}+^7iAWPE$r41q#?gwT(o~d^}XJ>(@VWBYOs;R9#0@FXPXO_3%IEGKX0S-"
    "BL?2?%$6E&r$NPSlxoB<iKMKyV5RQBqkc~-u83mq>_Dmr`8mCvg{&u2M9N`RT;#2i`n<%M<Dbp+tlG^X1%^hE)#&z%8oU$ZzIN}u"
    "++qV42&H(}DQtLz&;ut(c(Rf+)b0Dn9)itkETC$d(2D0jNzcS&R4(Q6eeCX)39X$=9cM>6yEtO{ZjF_}*PK#NYCVB=E%DmYt9H4!"
    "js4Ild9W2_-Zc-l=#bksj#C!sN2ZsM7@^~w1T|K7oZVQ6sum0C^A&JumUeEPwE4a-Ds7o^M(x(&L&+i%dceLA6h#OD%4aOHOTq9)"
    "KqZbI5NkZQdAB8eukDlD2h-(T!|<ieRT6sT+)Al^M(v_C&X7{l`-L7DB@)z^C*3H8qXz`0SuyiEuN9TH0ve;JmwczJ!;mOr5zSb{"
    "Wu4nTD>b%TGGGuJJM8Z_-CBf$*u-If>_G-X#yn=QoQH(H{uI(HT7Cfy14zBmtL2(KA+pP@Hg=g75<=@^Rc=Fnw%ZbzhDKzQld%eS"
    "y(o1|Z=B)C*M%*tDmW(1+bI1$77eUotisW&cf5$*j&l&9-mx6A0rJmrt6kal_0J`jW%Y6jJP_oPi9)DO?#rMH$h0tgd8`k=q0liC"
    "NLQf%(=Qe|OsLTrfZ~SG6{=axqF;yMQEv3NDveU|n%}4&abic`2<I~IIzs_jq#DQRb~KeN|MK*2JMKTD@)CM<4m?w3_6wUgx?;vg"
    ">&UjF`BCTJc7@nEbT>t?7g%>5uYjH2f<x??+s!$<*?Hi~x(jMWueTIwLG32$1xYCi0woZhB5`EgulD6aAERiF4sZE_4%|+qFSC7_"
    "iT)l?EsX`ddcCB=s=zuJ5%T&cIY`vPJ~V$t6-nM4>=vbkyz2_Ra@`Vf{1Zy83K@Pdd$fN^4q8BzMuJi+FXm|?W|T%;nYW12(F0bp"
    "Ma`BvE7_x0juMIrx!PBWUW$cHEd8tL?%0Z4>gy8y;s7zT3|H^p>G{)ejyXa5KcSZdj@(=w?2%(&qSY)+z;o<?0Lxj_;|KjDQ@$Yy"
    "byp3yd2_S+`mMJd!<%=jy9J=jm$rpE|9-R367>~&f4sHa(vV`v{l^dX)V^Cb;^i}2xfuOMeBtQzJ8pbq2Blu2OlmwbN~fgcjviPy"
    "JIa>}WZhCheP8I-t#tIjD8eMI&LF*JljQ**PB{y?elMYB$lM}XxAo_9gcB@k{!4rCQ;E%I)NW3&+4w>ae31wW3i$!{NXDX?ikiF0"
    "WHXtBmkT6oBWDy8MHRBz{(kg4KLgyTd|C}kV}gW%N3Vak<R0|zNBZbLbGykGQ7uZn<!Aa(3h@8y?8=hcIFjgj{D)qv`!I7CQiK`Q"
    "NU|k|V1p#c0YeK#jTiw@um+Bx!uJt~J51+NT`f=|-t!N>@}at`v#PRkdAWQ{1Rv~J?Dje!_0RfBCVBkXN}md3nd>=NxjZ}rYVOvK"
    "f(-)+5M@3V6@F>#BGc{me?D|*b~idUKBLuDrTw|^(?Qi$b&@BXUX`QXqag@2Hp(7FIW+}qySHL@t3l~bZkH$SR>4t=D`x*`4Miw+"
    "8Ta8|kBJ*r9rwBp1>b^ouk+cs&&~8u2Bp?x8H$Y)T78dT@f)$6GOi)SDbqct*<CN5Z>B5eWUqP@6?au^-D8O_t}be+CP4x(Wi*2?"
    "UlUtd=Jl|Gnvb#YPGj=-+Z8>O(POqsx47Um(l%z984B}4G$v03-$dJW-rkGbj|eB)?ORd1cg`Z-h~K{>Eb8ElA%enBcJba+hC;kI"
    "B5$50lgFQ}iKq$Vk5V_kFcvZTli7Xb!;+{S3En-;P>}Uy-?WoI8)Md5ndISj$!(o}SV_Sp6_zhO^ki7%<LcD42|}9(VG9cx3H9J1"
    "cUpR-$5mV&GC~G#L~O$TF2tq2n>|g$5EN{>sF&Vn0FUBYdp1Wg*$`RC90gwkbvAs?h4zRT%NEE=JC)$eFrlz*+`jMa{pLpx=4k6Y"
    "EQrgXZheOONF17xL}J~k-{ly)Wz<O?&m}SQ^3zzNe@Gd<rgN@8y^tAz%I=FKPvlVOrq^v;cy&eVSq6?G97;Ntq#lo%J75t}7m&W$"
    "G0|OSsT8d$qJDn?CAHbtSw6<YSbB8|j)GU5ypbK~io#|fPx3_ABEHe_6_Zb-Z}fQ&B8TWh113-0wQEBWVXw+b7X*dZlw{FR7bo)>"
    "rU`A5$FD7BI0^ahEpdr9!&_0<B_bqwBI~Vj6qk)<^R_PmO=u4(l00E>+6){?b^9ZNU&Q^)2866ZRk^>$T%^nvQHR2(t{RorDN^ey"
    "h>8LA_K5H3SE7pADme@V#SW|wn#mKNsc;nROVQ&ycht>OW-ObBg}AkeV<n=HdC;!0NgluT8;$8BB1uzCZbw0fQB1>ed3@`(E@s{S"
    "^FJcxtuiX=N6I{_L>*KbnjW=n`UgY<+fgqsr!4^S230+TxK`-19qi+}q>+xsQ9!IvS)Af1Z$B`*MC~YXQ=l;m?`ohZ$Wd<`(<TqC"
    "izdkvE4?rjmpEoS-hr^85MI+Fjs;hZ$XG@!ejs^RUl-4}dPw{zWikt8Lg6L6Sv5d0K7_)}6~l5BB!&AQ97`n{cW*jMZ^}6$3a@P)"
    "Vllr~`XU@RL*I)zVu7)mB##GoM)AEa_oT@3e9AIo74aP(F6P$k7k!L_qxH=nNHVGSq8-oHXSZ^^f_J^(c3lDz>#lSl?$~ML8XwQ_"
    "q(;ezFq-o53@Y{wQ3Hhl6TXVJaW5U8A-N4AZ~fFv9#4li#^>%fG2bVy2BGdzyK^1ONF8qS&{bj}PeksDh#Esz*UD!Y`Hre%Rgx$8"
    "A?;n}_;pfQG+IYJo3Pcr<_r{-hCSYT7Ka{%oyBdECn9JO^@^zwb$ysaJL<?YHeH@Lq3qc{5^3pjfwi$dqFIsFkk90aRPowT-|Ha%"
    "<NH+Rs0k4<DXaKKXH$lJCF@bN##$qU4ofl3)K!n7MpQTKHWqWnwh2X*jL17Sj$M4==f}tGPHGx!4LQa{7(&*m-SWnSyI$Q{s-=fd"
    "C3pets8ODZ-J4h8@B+=2v=!RP<K<ShM*szdJM>1eo8aMvWc9<m2*#x1D8hQF9fdOw7ar>uCapI!Nat-HOrEgVgQNaJBjalG6g>*F"
    "d8#CjKbyMs?v7@6Pd+f~sOVALZd1B*c!-6Zy=HYE&F=S!elXG6#=0iX<xbnJ-QAP9Frq_iDo^tG>c}E$wN=2Rv<yG(@^AeBZSmZn"
    "b~u{tw)14Z{&|9BueM2^ut7^l0iHgQx3kvd2@Q^;FjQlOtu99~+#n%3xfF}tc|wxMgD6o8<ys55^?ekgU|e+F-v!APR$VWWJYg5="
    "yF7h{kdmogSSEQQ%&EKiWK5i(P4r?<#?TG6@tl5_$D<&oZygE<C92LeNgf}?ZvGQ(*@`<F%+G5mW9-CZ0H&prBb@h4t<~TtI9E*l"
    "*F}$ls-euHGI=88>CZ+axU|u4rFAmGrO(`Ny<5Ct@p7GPFyh}wn=!xy+s1pH)$>rE$2LYs6w4L+x1LGt*ux7dcyBZvj%7JTn|ce2"
    "BzqOZH=XWFD&zxvxvhtXdwC*nvW=b^!=7BpZcm(jgSVrI0@`>gMeOc58EB3WFz%j{!B@kR07};rq7pd7UYC<2yd<EBlq~mA#y*Fz"
    "14+co9AQQo4P9^SbKeq;RZ7p2xto09Oe4Dzbg1`NjDem|nAw&mdE!9SQGS0RTP1Wz<w+iQPn*(qD5S+ka5^=Sr-JTUnJFkZ*sRai"
    "7>ZzH7&&KAhuShffNO)AZ$CiqW)V<h(Pw9au!_`iZJ0bUn~M5lL8NljPKqih&an}Cl(g8wuZeA3C)0hr_E)#;#!<@`%!Rw{QC!e3"
    "iyN_FkxXYZ2dCPO>Cr9GS)q+4_;jB#fT}X0?ls-|;XXC;vIaxReu`gv<Q=nwr5qTeco{Y<G@rT4<LN@NMqJ|UM+|RT<=Takp_{SW"
    "$^XtUU*}bi;<T~#9Nr-ob8Zb#R0z6_m&u3)#!7R-B#HQ{A()A3r&To+<_61?JZ@CgaTH0Z*u$^xI%3gdxip6?txz`2L9tbj<t`hd"
    ")lI^(yJZ!&u*f<pt2&`5%GWG9p{IO$MK)OPuR#47yd7~O$0xj`zJl+QIDcQ$_v2O+n;KK~`;xHHX)ky-K$MTtKTw*J$LsL`3u#WM"
    "6UwQI;SsYkVNG*(CYt4gJ%r?X(|62<*xiofe)pi-@8v$qX0jyC<#@8-Wvu#yt}|pIrmZ{e8h!P0{qiN=K}vg9jvU@8IkTxMHcMDG"
    "cg#H3isj6nD#rE)SSaJNNKXsN51)`Q=j?O5zB|}wV&)Nr6O7i*jBhCH5;Ty<uXz>=nZDi}V2l@TAgMetihZ3o(*MJB2^uSGqlgjn"
    "9*d3DBzZh`5{ihrU`!4li^xF^PTAa{zDGp(FqNR>viPBK4{a%sKkae`w2r1qu3RJE;LKWW=x0Yc`jCPni;7O)adCWGlg9-2k$&&e"
    "P&koD8+#((9nZcl_h@De%a&9ub%?gHu(!to4z?=E6Am`j%i|SPXHi5S_VJ3VUbmh1<O+}f=&6u9>hnH!Dilec7{yUip9_srCV3)G"
    ">+gbARVYoY%j5HGnG7daQY45_*tP?CqH4xxVC#wqWEJR1*M1)jP?YA;d^=fC6xNkF#!eQJ>PiwpyDR==NsQRUllEkZIIi`*g2@w9"
    "<nmsITCLwcMs2jlX_ySP``IMcStNPf)nTX3$?EPBX8H*IY7`V_^Cs<IL51QWX26>~eD-)n&FRmm9b{Jg>2snub`<LYP6-wpz1##x"
    "!RuL1Q=PZdmxP9g=(az7iR@@1KN=-@-1S~MipwB3E$UE{YbMXH{Vqz%MHW|3ACM*%WX=eBIO)P^o8oLP2jtF;TVgC#l1Hu=<}WdM"
    "{1cBHMI_i%qdcPILsQqsEFSqC7EjQu;)cecv_Mz4=-E4>thedsL{JE|v8%nwBZ)(1Dw#Zf+*oPB>>a{guV$Pskh8tJn`6dQ3WnPJ"
    "_6#$X>LgESo$7#O(qAxI=crEWh-4vKcZ%Zt)*&XF8us%(>0&8+EayQCF^PGAg*vX*15~%7pB&-7C>=B;IFeOm8;;2nyS;tHC7BIk"
    "A8|?5)mY~^L5-QlMrA@ljg5+dJYKtE!PpK32e&mRt#Q<xsj2oi;;5R+5K&CO$gD~z%y!C?JYhTeD58GEecLpAg><59%YGTIh-{)h"
    "AMfl|3?bY?vy_Ssb%|y9nh|31gp*s}=v>To#;f8eqHS>->#WYlL<&vo-DW$~W-?_C6rH{EpYNW$X1-MGD5|@FeJO3>jotG@k|%Uk"
    "wdni}M7k8I<y;<5Ju;)BL#-B=ky$2rV*jZOMX)YbF`4T84cZ7MG)bO#w%Sp+=QN8I3LT0fq|1FCsLC$uQ{15-7VkQmaOWTJc~B34"
    "&i0&Os8<_6*TVccWyrZla{l~o`IJe7sd^Mg=3<{%fn1z35+C<ifCwhN8lxEYgcCxYDkn4TPz3*V6Sw7yg)rd~%S7Mn)fcL{LS<Q("
    "9qQ8_;UKcbr6|nFQzv=ijr`e&a9j~{{azD!p-o>Rdk?k#^g<eGAh)?D{sTe^Q^e4M$rI**ZlRZZ)Xmg`E|+`j3nqMBL=-^fpf}Bs"
    "<cXE#C}J~=461@+3W$ubtV3;n!=l`y$b(=IV!~AkFS#@v>%J{c*Z(|b*vdvdis7h=W5NBhwc~T>QM;AAiT0bx<J+bZ|A|8wKk?;W"
    "W9m8vyVz&`Wr^klst@``i!b;=poysEcTr++N;6Qvt114*V1ELYztu4@!Q=@uLlxtO$>R%746Uer=9BqYcL!(KCu@^D@oYW{)o7}+"
    "9p>g*dXo^o)2c^t!R9^(GhzX^#y}pY95Q>ULm^c#MJze&<llb4&b21V<7a&ppNjEvJ4M3H_1z&u3TggrMR9(=CZ<*mu+TP`R|y5l"
    "4@M!j&G=qa|L)qgXmj`{mM7RIdE$!X-&dRl(B73Nd3+Sp?d1`7#SV_b-GdsaDjYS(7_rR;HhJRureEhX(ce}nqAEuLdGvZAZIV3h"
    ">eTS)<|#pgB2{=ABakx}ClboMs!mX6Ofb6gu_VtFx~GIBPsFe)MSbX=jmQXA_n@Je9j`FdW^zsJczHEIY2WbGg6NA~yVKbIfo=w)"
    "hM8lZ5;YBqO;1ken3wqwi^rsNzxoD?=#Lg7X9*=eoW>6o-by^EP4b-`{&7h>VV<yh{4os(tB|l(aY<-k`kHLce%|I=SSpWRuSiY$"
    "hv~kssu1bG)fN^ziM|<;&|Z1k!8f8h(aWhcn5&a3&ShE+#yx#bRU%i#0INYj;+fTtH^d?{oX4F|Q09ULXk@FQ9;$Pg*v;y1M#MW|"
    "C^j2nDSar4!MdBz?r!EBp-t`gtl>W(nJW3H-bNvsAMTAs`JJS0`rf$s+Q|m<Oc5psHs8W>JC%Ipd;dTX^|V9m?s=}$*~(b03AOoU"
    "wmH~is9=-+y9I)*)6oDmxkhR1>T(-JthH)@U9K<BsV=j5_y&GAeZ77=M$Ykiup@N~Tx*+%b=pR9jLmP)zApB$yL_GG39C4F)M`Ox"
    "zbLltu~0ptS%4-_1dAO-@GVGULuDwU`C04XNJC)(`hh&*6_3w`+^s5iAiF%#Da5}HRJzo<XWQiEcRXWuTAhc<l&%r4yorTl2~R~F"
    "5w2}jpTEw@<e2ag$sST0ipon2wkJ<!U;n(8ZYbU1b+K5#C5RV;+1P`B5QoXZz6ABUP3+&VH{%8IZ?+=z-;6eWefW&99E5m1Z2g0%"
    "J@pS}aoImCrm~aYEdSZ-)OG;rUrFbWx3_*R#hG5sw6K3TI8&Bb?jLH~JnbJk3-J8;dj960y-qWH9n}+Q;VGFO_&;RnA8zKj&slV%"
    "NH4Pa<-d$dqz@|RV|Nq$N3U=B51Yw5ydj@DirXGV_bRXh+OWh{V9$9?G}an9m5!PpN9$Ku!;fb44TK1Ym{u>*7?vyEl1MNJ@vxYV"
    "iJHsC>w`NK$U<f`KSCb|=XR=7F`<xAa?Rxv`7?%@-OPJML77Y1;GvVJu6vaoJ<|!E+^#whdK9JuS&}C-&E{=_)JEwjd6LIRF?Z#3"
    "LXe=uJ__2bdQ2E*rHv(w;X>a!-QCMaQCW{-p0G8P@SQwjn))c4(dPIiTIv}F@^}wLjll`({Dnl8XBWds_{IqtJPvNcSPfA~^2Ceh"
    "j++04z4$<$2uVcLd#0zF?eHB6sBzV28^{xcPyTGgbt8)*i4KKdAA%=?35v>N9GS9BMX_N{TC2s|9AA+;Lun|2MKgGbji9KC23rm%"
    "@8pf}u#VX$9qNX3&Ua^@mZfY?g?X4st1EgG7OrZOJkjM*pY808wDBh9ur-ueHNrN>xTC|U$8rQw5{M}h7IIo<Nq+Yz|N1{Qc~Lb"
)

def _load_and_resolve_schools():
    """압축 데이터를 디코딩하고 중복 학교명을 해결해 SCHOOL_LIST를 반환."""
    raw     = zlib.decompress(base64.b85decode(_SCHOOL_DATA_B85))
    rows    = json.loads(raw.decode("utf-8"))
    schools = [{"code": r[0], "name": r[1], "office": r[2], "type": r[3]} for r in rows]

    # 1) 교차-시도 충돌: (이름, 학교급)이 여러 교육청에 걸쳐 있음
    nt_offices = defaultdict(set)
    for s in schools:
        nt_offices[(s["name"], s["type"])].add(s["office"])

    # 2) 동일-교육청 충돌: 같은 교육청 내 (이름, 학교급) 코드 2개 이상
    ont_codes = defaultdict(list)
    for s in schools:
        ont_codes[(s["office"], s["name"], s["type"])].append(s["code"])

    # 기관 중 이름에 '학교'가 있는 것은 특수학교로 재분류
    for s in schools:
        if s["type"] == "기관" and "학교" in s["name"]:
            s["type"] = "특수학교"

    result = []
    for s in schools:
        base = s["name"]
        nt   = (base, s["type"])
        cross_offices = nt_offices[nt]
        intra_codes   = ont_codes[(s["office"], base, s["type"])]

        cross = len(cross_offices) > 1
        intra = len(intra_codes)   > 1

        if cross or intra:
            short = OFFICE_INFO.get(s["office"], {}).get("short", s["office"])
            city  = CODE_PREFIX_CITY.get(s["code"][:4], "")
            if intra and city:
                display = f"({short} {city}){base}"
            elif cross or intra:
                display = f"({short}){base}"
            else:
                display = base
        else:
            display = base

        result.append({**s, "name": display, "_raw_name": base})
    return result


SCHOOL_LIST  = _load_and_resolve_schools()
SCHOOL_NAMES = [s["name"] for s in SCHOOL_LIST]

SCHOOL_BY_TYPE = {
    "유치원":   [s for s in SCHOOL_LIST if s["type"] == "유치원"],
    "초등학교": [s for s in SCHOOL_LIST if s["type"] == "초등학교"],
    "중학교":   [s for s in SCHOOL_LIST if s["type"] == "중학교"],
    "고등학교": [s for s in SCHOOL_LIST if s["type"] == "고등학교"],
    "특수학교": [s for s in SCHOOL_LIST if s["type"] == "특수학교"],
    "기관":     [s for s in SCHOOL_LIST if s["type"] == "기관"],
}
ALL_TYPES = ["유치원", "초등학교", "중학교", "고등학교", "특수학교", "기관"]

# 교육청별 + 학교급별 인덱스 (빠른 필터링용)
SCHOOL_BY_OFFICE_TYPE = {}
for _oc in list(OFFICE_INFO.keys()) + ["전체"]:
    for _tp in ALL_TYPES:
        if _oc == "전체":
            SCHOOL_BY_OFFICE_TYPE[(_oc, _tp)] = [s for s in SCHOOL_LIST if s["type"] == _tp]
        else:
            SCHOOL_BY_OFFICE_TYPE[(_oc, _tp)] = [s for s in SCHOOL_LIST if s["type"] == _tp and s["office"] == _oc]

# 교육청별 전체 목록
SCHOOL_BY_OFFICE = defaultdict(list)
for s in SCHOOL_LIST:
    SCHOOL_BY_OFFICE[s["office"]].append(s)
SCHOOL_BY_OFFICE["전체"] = SCHOOL_LIST[:]

# ───────── 기본 학교: 신동초등학교(경북) ─────────
_default = next((s for s in SCHOOL_LIST if s["_raw_name"] == "신동초등학교" and s["office"] == "R10"), None)
if _default is None:
    _default = next((s for s in SCHOOL_LIST if "신동초등학교" in s["name"] and s["office"] == "R10"), None)
DEFAULT_SCHOOL = _default if _default else SCHOOL_BY_TYPE["초등학교"][0]

API_KEY  = "9bffa2116eb747c18a082f5e52617d37"
APP_NAME = "급식알리미"

# ─── 현재 선택된 학교 ───────────────────────────
_current_school = DEFAULT_SCHOOL.copy()
def get_office_code(): return _current_school["office"]
def get_school_code(): return _current_school["code"]
def get_school_name():  return _current_school["name"]



# ─── 시작프로그램 바로가기 ────────────────────────────────────
def get_exe_path():
    if getattr(sys, "frozen", False):
        return sys.executable
    return os.path.abspath(__file__)

def get_startup_folder():
    return os.path.join(
        os.environ.get("APPDATA", ""),
        r"Microsoft\Windows\Start Menu\Programs\Startup"
    )

def get_shortcut_path():
    return os.path.join(get_startup_folder(), f"{APP_NAME}.lnk")

def is_registered():
    return os.path.exists(get_shortcut_path())

def register_startup():
    import comtypes.client
    shell    = comtypes.client.CreateObject("WScript.Shell")
    shortcut = shell.CreateShortcut(get_shortcut_path())
    shortcut.TargetPath       = get_exe_path()
    shortcut.WorkingDirectory = os.path.dirname(get_exe_path())
    shortcut.Description      = "학교 급식 알리미"
    shortcut.save()

def register_startup_fallback():
    exe  = get_exe_path()
    lnk  = get_shortcut_path()
    wdir = os.path.dirname(exe)
    ps   = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$s = $ws.CreateShortcut("{lnk}"); '
        f'$s.TargetPath = "{exe}"; '
        f'$s.WorkingDirectory = "{wdir}"; '
        f'$s.Description = "학교 급식 알리미"; '
        f'$s.Save()'
    )
    import subprocess
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
        creationflags=0x08000000,
        check=True
    )

def unregister_startup():
    lnk = get_shortcut_path()
    if os.path.exists(lnk):
        os.remove(lnk)

def do_register():
    try:
        register_startup()
    except Exception:
        register_startup_fallback()


MEAL_NAMES = {1: "아침", 2: "점심", 3: "저녁"}

def _parse_menu(ddish_nm: str) -> str:
    menu = re.sub(r'\s*[\(\[]\d[\d\.\,\s]*[\)\]]', '', ddish_nm)
    return menu.replace("<br/>", "\n").strip()

def fetch_meal(date: datetime, office_code=None, school_code=None):
    """날짜의 아침/점심/저녁 급식을 모두 조회한다.
    반환: ({1: {...}, 2: {...}, 3: {...}}, error_str | None)
    각 키는 식사코드(int), 값은 menu/kcal/orplc 딕셔너리.
    데이터가 없는 식사 코드는 포함되지 않는다.
    """
    oc = office_code or get_office_code()
    sc = school_code or get_school_code()
    date_str = date.strftime("%Y%m%d")
    # MMEAL_SC_CODE 없이 요청 → 해당 날의 모든 식사 반환
    url = (
        "https://open.neis.go.kr/hub/mealServiceDietInfo"
        f"?Type=json&pIndex=1&pSize=10"
        f"&ATPT_OFCDC_SC_CODE={oc}"
        f"&SD_SCHUL_CODE={sc}"
        f"&MLSV_YMD={date_str}"
    )
    if API_KEY:
        url += f"&KEY={API_KEY}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return None, f"네트워크 오류:\n{e}"

    if "mealServiceDietInfo" not in data:
        code = data.get("RESULT", {}).get("CODE", "")
        msg  = data.get("RESULT", {}).get("MESSAGE", "알 수 없는 오류")
        if code == "INFO-200":
            return {}, None
        return None, f"API 오류 [{code}]\n{msg}"

    rows = data["mealServiceDietInfo"][1]["row"]
    result = {}
    for r in rows:
        mc = int(r["MMEAL_SC_CODE"])
        result[mc] = {
            "menu":  _parse_menu(r["DDISH_NM"]),
            "kcal":  r.get("CAL_INFO", "").strip(),
            "orplc": r.get("ORPLC_INFO", "").strip(),
        }
    return result, None


def fetch_week_meals(week_monday: datetime, office_code=None, school_code=None):
    oc = office_code or get_office_code()
    sc = school_code or get_school_code()
    friday = week_monday + timedelta(days=4)
    url = (
        "https://open.neis.go.kr/hub/mealServiceDietInfo"
        f"?Type=json&pIndex=1&pSize=20"
        f"&ATPT_OFCDC_SC_CODE={oc}"
        f"&SD_SCHUL_CODE={sc}"
        f"&MMEAL_SC_CODE=2"
        f"&MLSV_FROM_YMD={week_monday.strftime('%Y%m%d')}"
        f"&MLSV_TO_YMD={friday.strftime('%Y%m%d')}"
    )
    if API_KEY:
        url += f"&KEY={API_KEY}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return None, f"네트워크 오류:\n{e}"

    result = {}
    for i in range(5):
        d = week_monday + timedelta(days=i)
        result[d.strftime("%Y%m%d")] = {}

    if "mealServiceDietInfo" not in data:
        code = data.get("RESULT", {}).get("CODE", "")
        if code == "INFO-200":
            return result, None
        return None, data.get("RESULT", {}).get("MESSAGE", "알 수 없는 오류")

    day_rows = {}
    for row in data["mealServiceDietInfo"][1]["row"]:
        ymd = row.get("MLSV_YMD", "")
        if ymd not in result:
            continue
        mc = int(row["MMEAL_SC_CODE"])
        if ymd not in day_rows or mc == 2:
            day_rows[ymd] = row

    for ymd, row in day_rows.items():
        menu = re.sub(r'\s*[\(\[]\d[\d\.\,\s]*[\)\]]', '', row["DDISH_NM"])
        menu = menu.replace("<br/>", "\n").strip()
        result[ymd] = {
            "menu": menu,
            "kcal": row.get("CAL_INFO", "").strip(),
        }
    return result, None



# ─── 학교 선택 팝업 (교육청 → 학교급 탭 → 검색) ──────────────
class SchoolPicker(tk.Toplevel):
    BG    = "#F5FAF4"
    POINT = "#66BB6A"
    GRAY  = "#7A9A7E"
    TEXT  = "#2C3A2E"

    TAB_TYPES  = ["유치원", "초등학교", "중학교", "고등학교", "특수학교", "기관"]
    TAB_COLORS = {
        "유치원":   "#F48FB1",
        "초등학교": "#66BB6A",
        "중학교":   "#42A5F5",
        "고등학교": "#AB47BC",
        "특수학교": "#78909C",
        "기관":     "#FF8A65",
    }
    TAB_ICONS = {
        "유치원":   "🌸",
        "초등학교": "🌿",
        "중학교":   "📘",
        "고등학교": "🎓",
        "특수학교": "🏥",
        "기관":     "🏛️",
    }

    # 교육청 목록 (UI 표시용)
    OFFICE_DISPLAY = ["전체"] + [v["name"] for v in OFFICE_INFO.values()]
    OFFICE_CODE_BY_DISPLAY = {"전체": "전체",
                               **{v["name"]: k for k, v in OFFICE_INFO.items()}}
    OFFICE_DISPLAY_BY_CODE = {"전체": "전체",
                               **{k: v["name"] for k, v in OFFICE_INFO.items()}}

    def __init__(self, parent, current_school: dict, initial_tab: str = None):
        super().__init__(parent)
        self.title("다른 학교 보기")
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg=self.BG)
        self.result       = None
        self._current     = current_school
        cur_type          = current_school.get("type", "초등학교")
        self._active_tab  = (initial_tab or cur_type) if (initial_tab or cur_type) in self.TAB_TYPES else "초등학교"
        self._active_office = current_school.get("office", "전체")
        self._filtered    = {}
        self._build()
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")
        self._refresh_list()

    # ── 보조 ──────────────────────────────────────────────────
    def _schools_for_type(self, tab_type):
        return SCHOOL_BY_OFFICE_TYPE.get((self._active_office, tab_type), [])

    # ── UI 구성 ───────────────────────────────────────────────
    def _build(self):
        # 헤더
        hdr = tk.Frame(self, bg=self.POINT, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🏫  다른 학교 보기",
                 font=("맑은 고딕", 14, "bold"),
                 fg="white", bg=self.POINT).pack()

        # ── 교육청 선택 ─────────────────────────────────────
        oc_frame = tk.Frame(self, bg="#E8F5E9", pady=6)
        oc_frame.pack(fill="x", padx=0)
        tk.Label(oc_frame, text="🏢 교육청",
                 font=("맑은 고딕", 10, "bold"),
                 bg="#E8F5E9", fg="#2E7D32").pack(side="left", padx=(12, 6))
        self._office_var = tk.StringVar(
            value=self.OFFICE_DISPLAY_BY_CODE.get(self._active_office, "전체"))
        self._office_cb = ttk.Combobox(
            oc_frame, textvariable=self._office_var,
            values=self.OFFICE_DISPLAY,
            font=("맑은 고딕", 10), state="readonly", width=22)
        self._office_cb.pack(side="left", padx=(0, 12))
        self._office_cb.bind("<<ComboboxSelected>>", self._on_office_change)

        # ── 학교급 탭 ─────────────────────────────────────────
        tab_frame = tk.Frame(self, bg="#DCF0DC")
        tab_frame.pack(fill="x")
        self._tab_btns = {}
        for t in self.TAB_TYPES:
            color = self.TAB_COLORS[t]
            icon  = self.TAB_ICONS[t]
            cnt   = len(self._schools_for_type(t))
            btn   = tk.Button(
                tab_frame,
                text=f"{icon}\n{t}({cnt})",
                font=("맑은 고딕", 8, "bold"),
                relief="flat", bd=0, cursor="hand2",
                padx=4, pady=6,
                command=lambda tt=t: self._switch_tab(tt)
            )
            btn.pack(side="left", fill="x", expand=True)
            self._tab_btns[t] = (btn, color)
        self._refresh_tabs()

        # ── 검색창 ─────────────────────────────────────────────
        sf = tk.Frame(self, bg=self.BG, pady=8)
        sf.pack(fill="x", padx=14)
        tk.Label(sf, text="🔍", font=("Arial", 12), bg=self.BG).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())
        entry = tk.Entry(sf, textvariable=self._search_var,
                         font=("맑은 고딕", 12), relief="flat", bg="#FFFFFF",
                         highlightbackground="#CCDDCC", highlightthickness=1)
        entry.pack(side="left", fill="x", expand=True, padx=(6, 0), ipady=4)
        entry.focus_set()

        # ── 학교 수 ────────────────────────────────────────────
        self._count_var = tk.StringVar()
        tk.Label(self, textvariable=self._count_var,
                 font=("맑은 고딕", 9), bg=self.BG, fg=self.GRAY).pack(anchor="e", padx=14)

        # ── 목록 ───────────────────────────────────────────────
        lf = tk.Frame(self, bg=self.BG)
        lf.pack(fill="both", expand=True, padx=14, pady=(0, 4))
        sb = ttk.Scrollbar(lf, orient="vertical")
        act_color = self.TAB_COLORS.get(self._active_tab, self.POINT)
        self._listbox = tk.Listbox(
            lf, font=("맑은 고딕", 12),
            selectbackground=act_color, selectforeground="white",
            activestyle="none", relief="flat", bd=0,
            highlightthickness=1, highlightbackground="#CCDDCC",
            yscrollcommand=sb.set, height=16, width=26, cursor="hand2")
        sb.config(command=self._listbox.yview)
        self._listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._listbox.bind("<Double-Button-1>", lambda e: self._select())
        self._listbox.bind("<Return>",           lambda e: self._select())

        # ── 하단 버튼 ─────────────────────────────────────────
        br = tk.Frame(self, bg=self.BG, pady=8)
        br.pack(fill="x", padx=14)
        self._ok_btn = tk.Button(br, text="✅  선택",
                  font=("맑은 고딕", 11, "bold"),
                  bg=self.POINT, fg="white", relief="flat",
                  padx=16, pady=6, cursor="hand2", bd=0,
                  command=self._select)
        self._ok_btn.pack(side="left", fill="x", expand=True)
        tk.Frame(br, bg=self.BG, width=8).pack(side="left")
        tk.Button(br, text="취소",
                  font=("맑은 고딕", 11),
                  bg="#BBBBBB", fg="white", relief="flat",
                  padx=16, pady=6, cursor="hand2", bd=0,
                  command=self.destroy).pack(side="left", fill="x", expand=True)

    # ── 이벤트 ───────────────────────────────────────────────
    def _on_office_change(self, _=None):
        name = self._office_var.get()
        self._active_office = self.OFFICE_CODE_BY_DISPLAY.get(name, "전체")
        self._filtered = {}
        self._search_var.set("")
        self._refresh_tabs()
        self._refresh_list()

    def _refresh_tabs(self):
        for t, (btn, color) in self._tab_btns.items():
            cnt  = len(self._schools_for_type(t))
            icon = self.TAB_ICONS[t]
            text = f"{icon}\n{t}({cnt})"
            if t == self._active_tab:
                btn.configure(bg=color, fg="white", text=text)
            else:
                btn.configure(bg="#DCF0DC", fg="#557755", text=text)

    def _switch_tab(self, tab_type):
        self._active_tab = tab_type
        self._search_var.set("")
        self._filtered[tab_type] = self._schools_for_type(tab_type)[:]
        color = self.TAB_COLORS.get(tab_type, self.POINT)
        self._listbox.configure(selectbackground=color)
        self._ok_btn.configure(bg=color)
        self._refresh_tabs()
        self._refresh_list()

    def _on_search(self):
        q = self._search_var.get().strip()
        t = self._active_tab
        base = self._schools_for_type(t)
        if q:
            self._filtered[t] = [s for s in base if q in s["name"]]
        else:
            self._filtered[t] = base[:]
        self._refresh_list()

    def _refresh_list(self):
        self._listbox.delete(0, "end")
        t = self._active_tab
        if t not in self._filtered:
            self._filtered[t] = self._schools_for_type(t)[:]
        lst = self._filtered[t]
        unit = "개 기관" if t == "기관" else "개 학교"
        self._count_var.set(f"{len(lst)}{unit}")
        sel_idx = None
        for i, s in enumerate(lst):
            self._listbox.insert("end", f"  {s['name']}")
            if s["code"] == self._current.get("code"):
                sel_idx = i
        if sel_idx is not None:
            self._listbox.selection_set(sel_idx)
            self._listbox.see(sel_idx)
        elif lst:
            self._listbox.see(0)

    def _select(self):
        idxs = self._listbox.curselection()
        if not idxs:
            return
        self.result = self._filtered[self._active_tab][idxs[0]]
        self.destroy()


# ─── 한 주 보기 팝업 (가로 5열) ──────────────────────────────
class WeekView(tk.Toplevel):
    BG      = "#FFF8F0"
    POINT   = "#FF6B35"
    GRAY    = "#888888"
    TEXT    = "#2D2D2D"
    CARD    = "#FFFFFF"
    TODAY   = "#FFE8D6"
    COL_W   = 170
    COL_PAD = 5

    def __init__(self, parent, base_date: datetime, office_code: str, school_code: str, school_name: str, on_school_change=None):
        super().__init__(parent)
        self.title(f"주간 급식표 — {school_name}")
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg=self.BG)

        self._today            = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        self._monday           = base_date - timedelta(days=base_date.weekday())
        self._office_code      = office_code
        self._school_code      = school_code
        self._school_name      = school_name
        self._school_obj       = next((s for s in SCHOOL_LIST if s["code"] == school_code), None) or \
                                 {"name": school_name, "office": office_code, "code": school_code, "type": "초등학교"}
        self._on_school_change = on_school_change

        self._build()
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h   = self.winfo_reqwidth(), self.winfo_reqheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
        self._load_week()

    def _build(self):
        hdr = tk.Frame(self, bg=self.POINT, pady=10)
        hdr.pack(fill="x")
        tk.Button(hdr, text="◀  지난주", command=self._prev_week,
                  bg=self.POINT, fg="white", relief="flat",
                  font=("맑은 고딕", 11, "bold"), cursor="hand2", bd=0,
                  padx=14, pady=4).pack(side="left")
        tk.Button(hdr, text="다음주  ▶", command=self._next_week,
                  bg=self.POINT, fg="white", relief="flat",
                  font=("맑은 고딕", 11, "bold"), cursor="hand2", bd=0,
                  padx=14, pady=4).pack(side="right")
        self._title_var = tk.StringVar()
        tk.Label(hdr, textvariable=self._title_var,
                 font=("맑은 고딕", 13, "bold"),
                 fg="white", bg=self.POINT).pack(expand=True)

        school_row = tk.Frame(self, bg="#FFE8D6", pady=4)
        school_row.pack(fill="x")
        tk.Label(school_row, text="🏫", font=("맑은 고딕", 10),
                 bg="#FFE8D6", fg="#CC4400").pack(side="left", padx=(10, 4))
        self._week_school_var = tk.StringVar(value=self._school_name)
        tk.Button(school_row, textvariable=self._week_school_var,
                  font=("맑은 고딕", 10, "bold"),
                  bg="#FFE8D6", fg=self.POINT, relief="flat",
                  cursor="hand2", bd=0, activebackground="#FFE8D6",
                  activeforeground="#CC4400",
                  command=self._open_school_picker).pack(side="left")
        tk.Button(school_row, text="변경",
                  font=("맑은 고딕", 9), bg=self.POINT, fg="white",
                  relief="flat", cursor="hand2", bd=0, padx=8, pady=2,
                  command=self._open_school_picker).pack(side="right", padx=10)

        self._status_var = tk.StringVar(value="⏳ 불러오는 중...")
        tk.Label(self, textvariable=self._status_var,
                 font=("맑은 고딕", 10), bg=self.BG, fg=self.GRAY).pack(pady=(6, 4))

        grid = tk.Frame(self, bg=self.BG)
        grid.pack(padx=10, pady=(0, 10))

        DAY_KR = ["월", "화", "수", "목", "금"]
        self._cells = []

        for i in range(5):
            col_frame = tk.Frame(grid, bg=self.CARD,
                                 highlightbackground="#DDDDDD",
                                 highlightthickness=1,
                                 width=self.COL_W)
            col_frame.grid(row=0, column=i,
                           padx=self.COL_PAD//2, pady=0,
                           sticky="nsew")
            col_frame.grid_propagate(False)

            hdr_bar = tk.Frame(col_frame, bg=self.POINT, height=38)
            hdr_bar.pack(fill="x")

            day_lbl = tk.Label(hdr_bar, text=DAY_KR[i],
                               font=("맑은 고딕", 13, "bold"),
                               fg="white", bg=self.POINT)
            day_lbl.pack(expand=True)

            date_lbl = tk.Label(col_frame, text="",
                                font=("맑은 고딕", 9),
                                bg=self.CARD, fg=self.GRAY)
            date_lbl.pack(anchor="center", pady=(4, 2))

            menu_lbl = tk.Label(col_frame, text="",
                                font=("맑은 고딕", 10),
                                bg=self.CARD, fg=self.TEXT,
                                justify="left",
                                wraplength=self.COL_W - 16,
                                anchor="nw")
            menu_lbl.pack(anchor="nw", padx=8, pady=(0, 4), fill="x")

            kcal_lbl = tk.Label(col_frame, text="",
                                font=("맑은 고딕", 8),
                                bg=self.CARD, fg=self.GRAY)
            kcal_lbl.pack(anchor="e", padx=8, pady=(0, 8))

            self._cells.append({
                "frame": col_frame, "hdr_bar": hdr_bar,
                "day_lbl": day_lbl, "date_lbl": date_lbl,
                "menu_lbl": menu_lbl, "kcal_lbl": kcal_lbl,
            })

        # 하단 닫기 버튼
        tk.Button(self, text="닫기",
                  font=("맑은 고딕", 10), bg="#888", fg="white",
                  relief="flat", cursor="hand2", bd=0, padx=16, pady=5,
                  command=self.destroy).pack(pady=(0, 10))

    def _open_school_picker(self):
        picker = SchoolPicker(self, self._school_obj)
        self.wait_window(picker)
        if picker.result:
            s = picker.result
            self._school_obj    = s
            self._office_code   = s["office"]
            self._school_code   = s["code"]
            self._school_name   = s["name"]
            self._week_school_var.set(s["name"])
            self.title(f"주간 급식표 — {s['name']}")
            if self._on_school_change:
                self._on_school_change(s)
            self._load_week()

    def _update_title(self):
        mon = self._monday
        fri = mon + timedelta(days=4)
        self._title_var.set(
            f"{mon.strftime('%Y.%m.%d')} — {fri.strftime('%m.%d')}  점심 급식"
        )

    def _prev_week(self):
        self._monday -= timedelta(weeks=1)
        self._load_week()

    def _next_week(self):
        self._monday += timedelta(weeks=1)
        self._load_week()

    def _load_week(self):
        self._update_title()
        self._status_var.set("⏳ 불러오는 중...")
        monday = self._monday
        oc     = self._office_code
        sc     = self._school_code
        def _fetch():
            result = fetch_week_meals(monday, oc, sc)
            self.after(0, lambda: self._render(*result))
        threading.Thread(target=_fetch, daemon=True).start()

    def _render(self, data, err):
        self._status_var.set("")
        for i, c in enumerate(self._cells):
            d        = self._monday + timedelta(days=i)
            ymd      = d.strftime("%Y%m%d")
            info     = data.get(ymd, {}) if data else {}
            is_today = (d == self._today)

            bg     = self.TODAY if is_today else self.CARD
            border = self.POINT if is_today else "#DDDDDD"
            bw     = 2          if is_today else 1
            hdr_bg = "#CC4400"  if is_today else self.POINT

            c["frame"].configure(bg=bg, highlightbackground=border, highlightthickness=bw)
            c["hdr_bar"].configure(bg=hdr_bg)
            c["day_lbl"].configure(bg=hdr_bg)
            c["date_lbl"].configure(bg=bg, text=d.strftime("%m/%d") + (" ★" if is_today else ""))
            c["menu_lbl"].configure(bg=bg)
            c["kcal_lbl"].configure(bg=bg)

            if err:
                c["menu_lbl"].configure(text="❌ 오류", fg="#CC0000")
                c["kcal_lbl"].configure(text="")
            elif info and info.get("menu"):
                c["menu_lbl"].configure(text=info["menu"], fg=self.TEXT)
                c["kcal_lbl"].configure(text=f"🔥 {info['kcal']}" if info.get("kcal") else "")
            else:
                c["menu_lbl"].configure(text="🚫\n급식 없음", fg="#BBBBBB")
                c["kcal_lbl"].configure(text="")



# ─── 달력 팝업 ───────────────────────────────────────────────
class DatePicker(tk.Toplevel):
    DAY_BG   = "#FFFFFF"
    SEL_BG   = "#FF6B35"
    TODAY_BG = "#FFE0CC"
    HEADER   = "#FF6B35"

    def __init__(self, parent, current: datetime):
        super().__init__(parent)
        self.title("날짜 선택")
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg="#FFF8F0")
        self.result    = None
        self._today    = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        self._viewing  = current.replace(day=1)
        self._selected = current
        self._build()
        self._render_calendar()
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _build(self):
        hdr = tk.Frame(self, bg=self.HEADER)
        hdr.pack(fill="x")
        tk.Button(hdr, text="◀", command=self._prev_month,
                  bg=self.HEADER, fg="white", relief="flat",
                  font=("맑은 고딕", 12, "bold"), cursor="hand2", bd=0,
                  padx=12, pady=6).pack(side="left")
        tk.Button(hdr, text="▶", command=self._next_month,
                  bg=self.HEADER, fg="white", relief="flat",
                  font=("맑은 고딕", 12, "bold"), cursor="hand2", bd=0,
                  padx=12, pady=6).pack(side="right")
        self._month_var = tk.StringVar()
        tk.Label(hdr, textvariable=self._month_var,
                 font=("맑은 고딕", 13, "bold"), fg="white", bg=self.HEADER).pack(expand=True)

        dow = tk.Frame(self, bg="#FFE8D6")
        dow.pack(fill="x")
        for i, d in enumerate(["일","월","화","수","목","금","토"]):
            c = "#CC3300" if i == 0 else ("#0044CC" if i == 6 else "#333333")
            tk.Label(dow, text=d, width=4, font=("맑은 고딕", 10, "bold"),
                     bg="#FFE8D6", fg=c).grid(row=0, column=i, pady=4)

        self._cal_frame = tk.Frame(self, bg="#FFF8F0")
        self._cal_frame.pack(padx=8, pady=(0, 8))

        br = tk.Frame(self, bg="#FFF8F0")
        br.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(br, text="오늘로 이동", command=self._go_today,
                  font=("맑은 고딕", 10), bg="#666", fg="white",
                  relief="flat", cursor="hand2", bd=0, padx=8, pady=4).pack(side="left")
        tk.Button(br, text="취소", command=self.destroy,
                  font=("맑은 고딕", 10), bg="#AAAAAA", fg="white",
                  relief="flat", cursor="hand2", bd=0, padx=8, pady=4).pack(side="right")

    def _render_calendar(self):
        for w in self._cal_frame.winfo_children():
            w.destroy()
        import calendar
        y, m = self._viewing.year, self._viewing.month
        self._month_var.set(f"{y}년 {m:02d}월")
        start_col = (self._viewing.weekday() + 1) % 7
        days = calendar.monthrange(y, m)[1]
        col = start_col; row = 0
        for day in range(1, days + 1):
            d = datetime(y, m, day)
            sel   = d == self._selected.replace(hour=0, minute=0, second=0, microsecond=0)
            today = d == self._today
            if sel:     bg, fg = self.SEL_BG, "white"
            elif today: bg, fg = self.TODAY_BG, "#CC3300"
            else:
                bg = self.DAY_BG
                fg = "#CC3300" if col==0 else ("#0044CC" if col==6 else "#2D2D2D")
            tk.Button(self._cal_frame, text=str(day), width=3,
                      font=("맑은 고딕", 11), bg=bg, fg=fg,
                      relief="flat", cursor="hand2", bd=0,
                      command=lambda dt=d: self._select(dt)
                      ).grid(row=row, column=col, padx=2, pady=2, ipady=3)
            col += 1
            if col > 6: col, row = 0, row+1

    def _prev_month(self):
        y, m = self._viewing.year, self._viewing.month - 1
        if m == 0: m, y = 12, y-1
        self._viewing = datetime(y, m, 1); self._render_calendar()

    def _next_month(self):
        y, m = self._viewing.year, self._viewing.month + 1
        if m == 13: m, y = 1, y+1
        self._viewing = datetime(y, m, 1); self._render_calendar()

    def _go_today(self):
        self._selected = self._today
        self._viewing  = self._today.replace(day=1)
        self._render_calendar()

    def _select(self, d):
        self.result = d; self.destroy()



# ─── 설정 저장/불러오기 ──────────────────────────────────────
import json as _json

def _config_path():
    base = os.path.join(os.environ.get("APPDATA",""), APP_NAME) \
           if sys.platform == "win32" else \
           os.path.join(os.path.expanduser("~"), f".{APP_NAME}")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "settings.json")

def load_settings() -> dict:
    try:
        with open(_config_path(), encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return {}

def save_settings(data: dict):
    try:
        with open(_config_path(), "w", encoding="utf-8") as f:
            _json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass



# ─── 밥풀이 캐릭터 (Canvas 오버레이 팝업 애니메이션) ────────────
# ── 학교급별 점심 권장 칼로리 (한국인 영양소 섭취기준 1/3 기준) ──
RECOMMENDED_LUNCH_KCAL = {
    "유치원":   460,
    "초등학교": 600,
    "중학교":   750,
    "고등학교": 850,
    "특수학교": 650,
    "기관":     780,
}
# ── 학교급별 1일 권장 칼로리 (조식+중식+석식 합산 비교용) ──
RECOMMENDED_DAILY_KCAL = {
    "유치원":   1400,
    "초등학교": 1800,
    "중학교":   2250,
    "고등학교": 2350,
    "특수학교": 2000,
    "기관":     2300,
}
KCAL_MARGIN = 0.15   # ±15% 적정 범위

# 팝업 표시용 학교급 이름 (기관→성인)
TYPE_DISPLAY_NAME = {
    "유치원":   "유치원",
    "초등학교": "초등학교",
    "중학교":   "중학교",
    "고등학교": "고등학교",
    "특수학교": "특수학교",
    "기관":     "성인(기관)",
}

TYPE_COLOR_MAP = {
    "유치원":"#F48FB1","초등학교":"#66BB6A","중학교":"#42A5F5",
    "고등학교":"#AB47BC","특수학교":"#78909C","기관":"#FF8A65",
}

def _day_total_kcal(day_data: dict) -> float:
    """하루치 급식 딕셔너리 {mc: kcal} → 합산 kcal."""
    return sum(day_data.values())

def _get_rec(school_type: str, is_full_day: bool) -> int:
    """학교급 + 전일 여부에 따른 권장 칼로리 반환."""
    if is_full_day:
        return RECOMMENDED_DAILY_KCAL.get(school_type, 2000)
    return RECOMMENDED_LUNCH_KCAL.get(school_type, 650)

def _is_full_day(data: dict) -> bool:
    """급식 데이터에 조식(1)+중식(2)+석식(3) 모두 있으면 True."""
    if not data:
        return False
    return any(1 in v and 2 in v and 3 in v for v in data.values())

def _judge(avg: float, rec: int) -> str:
    lo, hi = rec * (1 - KCAL_MARGIN), rec * (1 + KCAL_MARGIN)
    if avg < lo:   return "에너지 부족"
    elif avg > hi: return "에너지 과다"
    else:          return "에너지 적절"

def _week_number_in_month(d: datetime) -> int:
    """해당 날짜가 그 달의 몇 주차인지 반환 (1-based, 월요일 기준)."""
    first = d.replace(day=1)
    return (d.day + first.weekday() - 1) // 7 + 1

def get_kcal_judge(kcal_str: str, school_type: str):
    """
    kcal_str: "801.7 Kcal" 형태  → (line1, line2, bubble_color)
    """
    try:
        val = float(re.search(r"[\d.]+", kcal_str).group())
    except Exception:
        return ("냠냠~", "", "#E67E00")
    rec = RECOMMENDED_LUNCH_KCAL.get(school_type, 650)
    status = _judge(val, rec)
    colors = {"에너지 적절": "#43A047", "에너지 부족": "#2196F3", "에너지 과다": "#E53935"}
    return ("냠냠~", status, colors[status])




class BapPuri(tk.Canvas):
    """
    밥풀이 캐릭터 — 급식 카드 위에 오버레이로 팝업 슬라이드인.
    말풍선은 Canvas 상단에 항상 고정(가려지지 않음).
    """
    W = 140
    H = 170

    def __init__(self, master, bg="#F0F7EE", on_click=None):
        super().__init__(master, width=self.W, height=self.H,
                         bg=bg, highlightthickness=0)
        self._bg        = bg
        self._visible   = False
        self._anim_id   = None
        self._phase     = 0.0
        self._slide_y   = -self.H
        self._sliding   = False
        self._msg1      = "냠냠~"
        self._msg2      = ""
        self._msg_col   = "#E67E00"
        self._tap_visible = True   # 눌러봐~! 깜빡임 상태
        self._tap_count   = 0
        if on_click:
            self._on_click = on_click
            self.bind("<Button-1>", lambda e: on_click())
            self.configure(cursor="hand2")
        else:
            self._on_click = None

    # ── 공개 ─────────────────────────────────────────────────
    def show(self, msg1="냠냠~", msg2="", msg_color="#E67E00"):
        if self._anim_id:
            self.after_cancel(self._anim_id)
        self._msg1    = msg1
        self._msg2    = msg2
        self._msg_col = msg_color
        self._visible = True
        self._slide_y = -self.H
        self._sliding = True
        self._animate()

    def hide(self):
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None
        self._visible = False
        self._sliding = False
        self.delete("all")
        self.place_forget()

    # ── 내부 ─────────────────────────────────────────────────
    def _animate(self):
        if not self._visible:
            return
        import math
        if self._sliding:
            self._slide_y += 9
            if self._slide_y >= 0:
                self._slide_y = 0
                self._sliding = False
        self._phase += 0.10
        bounce = math.sin(self._phase) * 5
        # 눌러봐~! 깜빡임: 슬라이드 완료 후 15프레임마다 토글
        if not self._sliding:
            self._tap_count += 1
            if self._tap_count % 15 == 0:
                self._tap_visible = not self._tap_visible
        self._draw(offset_y=self._slide_y + bounce)
        self._anim_id = self.after(35, self._animate)

    def _draw(self, offset_y=0):
        self.delete("all")
        if not self._visible:
            return
        cx = self.W // 2
        # 캐릭터 몸통 중심 — 말풍선 공간 확보를 위해 아래쪽에 배치
        cy = 108 + int(offset_y)

        # ── 말풍선 (Canvas 상단 고정 — 항상 보임) ────────────
        bx1, by1, bx2, by2 = 4, 4, self.W - 4, 44
        # 배경
        self.create_oval(bx1, by1, bx2, by2,
                         fill="#FFFDE7", outline="#FFD54F", width=1)
        # 꼬리 (아래 방향 → 캐릭터 쪽)
        tail_cx = cx - 8
        self.create_polygon(tail_cx - 6, by2 - 2,
                            tail_cx + 6, by2 - 2,
                            tail_cx,     by2 + 10,
                            fill="#FFFDE7", outline="#FFD54F")
        # 텍스트
        mid_y = (by1 + by2) // 2
        if self._msg2:
            self.create_text(cx, mid_y - 7,  text=self._msg1,
                             font=("맑은 고딕", 9, "bold"), fill=self._msg_col)
            self.create_text(cx, mid_y + 7,  text=self._msg2,
                             font=("맑은 고딕", 8, "bold"), fill=self._msg_col)
        else:
            self.create_text(cx, mid_y, text=self._msg1,
                             font=("맑은 고딕", 9, "bold"), fill=self._msg_col)

        # ── 캐릭터 몸 (아래 영역) ────────────────────────────
        # 그림자
        self.create_oval(cx-30, cy+34, cx+30, cy+42,
                         fill="#C8C8C8", outline="", stipple="gray50")
        # 그릇 받침
        self.create_arc(cx-36, cy+12, cx+36, cy+44,
                        start=0, extent=-180,
                        fill="#DEC895", outline="#B89A58", width=2, style="chord")
        # 그릇 몸체
        self.create_arc(cx-32, cy-6, cx+32, cy+30,
                        start=180, extent=180,
                        fill="#F2E4C0", outline="#B89A58", width=2, style="chord")
        # 밥 돔
        self.create_oval(cx-27, cy-26, cx+27, cy+12,
                         fill="#FFFEFA", outline="#EAE0CC", width=1)
        # 밥 결
        self.create_arc(cx-20, cy-22, cx+5, cy+4,
                        start=40, extent=110, fill="", outline="#E8E2D0", width=1)
        self.create_arc(cx-5, cy-22, cx+20, cy+4,
                        start=40, extent=110, fill="", outline="#E8E2D0", width=1)
        # 얼굴
        fy = cy - 38
        # 볼
        self.create_oval(cx-22, fy+6, cx-11, fy+14,
                         fill="#FFB3BA", outline="", stipple="gray75")
        self.create_oval(cx+11, fy+6, cx+22, fy+14,
                         fill="#FFB3BA", outline="", stipple="gray75")
        # 눈 (에너지 상태에 따라 표정 변화)
        if self._msg2 == "에너지 과다":
            # 찡그린 눈
            self.create_arc(cx-18, fy+2, cx-7, fy+12,
                            start=180, extent=180, fill="#3A3A3A", outline="", style="chord")
            self.create_arc(cx+7, fy+2, cx+18, fy+12,
                            start=180, extent=180, fill="#3A3A3A", outline="", style="chord")
        else:
            # 기본 눈
            self.create_arc(cx-18, fy, cx-7, fy+10,
                            start=0, extent=180, fill="#3A3A3A", outline="", style="chord")
            self.create_arc(cx+7,  fy, cx+18, fy+10,
                            start=0, extent=180, fill="#3A3A3A", outline="", style="chord")
        # 눈 하이라이트
        self.create_oval(cx-15, fy+1, cx-12, fy+4, fill="white", outline="")
        self.create_oval(cx+10, fy+1, cx+13, fy+4, fill="white", outline="")
        # 입
        if self._msg2 == "에너지 부족":
            # 슬픈 입
            self.create_arc(cx-9, fy+12, cx+9, fy+22,
                            start=20, extent=140, fill="", outline="#3A3A3A", width=2)
        else:
            # 웃는 입
            self.create_arc(cx-9, fy+8, cx+9, fy+20,
                            start=200, extent=140, fill="", outline="#3A3A3A", width=2)
        # 팔
        self.create_oval(cx-40, cy,   cx-26, cy+14,
                         fill="#FFFEFA", outline="#E0D8C0", width=1)
        self.create_oval(cx+26, cy,   cx+40, cy+14,
                         fill="#FFFEFA", outline="#E0D8C0", width=1)

        # ── "눌러봐~!" 깜빡이는 텍스트 (밥그릇 위, 클릭 유도) ──
        if self._on_click and self._tap_visible and not self._sliding:
            tap_y = cy - 30
            # 배경 pill
            self.create_oval(cx-32, tap_y-12, cx+32, tap_y+12,
                             fill="#FF5722", outline="#FF3D00", width=1)
            self.create_text(cx, tap_y, text="눌러봐~! 👆",
                             font=("맑은 고딕", 8, "bold"), fill="white")





# ─── 월별+주별 칼로리 분석 팝업 ────────────────────────────────
import queue as _queue

class MonthlyKcalPopup(tk.Toplevel):
    BG = "#FAFAFA"
    STATUS_INFO = {
        "에너지 적절": {"color":"#43A047","bg":"#E8F5E9","icon":"😊","face":"normal"},
        "에너지 부족": {"color":"#1E88E5","bg":"#E3F2FD","icon":"😢","face":"sad"},
        "에너지 과다": {"color":"#E53935","bg":"#FFEBEE","icon":"😤","face":"angry"},
        "데이터 없음": {"color":"#9E9E9E","bg":"#F5F5F5","icon":"😶","face":"normal"},
    }
    TYPE_COLOR = {
        "유치원":"#F48FB1","초등학교":"#66BB6A","중학교":"#42A5F5",
        "고등학교":"#AB47BC","특수학교":"#78909C","기관":"#FF8A65",
    }

    def __init__(self, parent, year, month, week_monday,
                 school, office_code, school_code):
        super().__init__(parent)
        self.title("📊 급식 칼로리 분석")
        self.resizable(True, True)
        self.grab_set()
        self.configure(bg=self.BG)
        self._parent   = parent
        self._school   = school
        self._oc       = office_code
        self._sc       = school_code
        self._stype    = school.get("type", "초등학교")
        self._m_year   = year
        self._m_month  = month
        self._w_monday = week_monday
        self._m_cache  = {}          # {(year,month): day_data}
        self._q        = _queue.Queue()
        self._build()
        self.update_idletasks()
        self._position_next_to_parent()
        self._poll()
        self._load_both()

    # ── 위치: 메인 창 오른쪽에 밀착 ─────────────────────────
    def _position_next_to_parent(self):
        self.update_idletasks()
        pw  = self._parent.winfo_width()
        px  = self._parent.winfo_rootx()
        py  = self._parent.winfo_rooty()
        sw  = self.winfo_screenwidth()
        sh  = self.winfo_screenheight()
        pw2 = self.winfo_reqwidth()
        ph2 = self.winfo_reqheight()
        rx  = px + pw + 4
        if rx + pw2 > sw:
            rx = max(0, px - pw2 - 4)
        ry = py
        if ry + ph2 > sh:
            ry = max(0, sh - ph2)
        self.geometry(f"+{rx}+{ry}")

    def _tc(self): return self.TYPE_COLOR.get(self._stype, "#66BB6A")
    def _sd(self): return TYPE_DISPLAY_NAME.get(self._stype, self._stype)
    def _clr(self, f):
        for w in list(f.winfo_children()):
            try: w.destroy()
            except: pass
    def _ldg(self, f):
        tk.Label(f, text="⏳ 데이터 불러오는 중…",
                 font=("맑은 고딕",10), bg=self.BG, fg="#888888").pack(anchor="w", pady=6)

    # ── 큐 폴링 ─────────────────────────────────────────────
    def _poll(self):
        for _ in range(10):
            try:
                msg = self._q.get_nowait()
                tag = msg[0]
                if tag == "month":
                    # msg = ("month", data, err, year, month, w_monday_snapshot)
                    _, data, err, yr, mo, w_snap = msg
                    self._do_render_month(data, err, yr, mo, w_snap)
                elif tag == "week":
                    # msg = ("week", data, err, w_monday_snapshot)
                    _, data, err, w_snap = msg
                    self._do_render_week(data, err, w_snap)
            except _queue.Empty:
                break
            except Exception as e:
                try:
                    for f in (self._mf, self._wf):
                        self._clr(f)
                        tk.Label(f, text=f"오류: {e}",
                                 font=("맑은 고딕",9), bg=self.BG, fg="#C62828").pack(anchor="w")
                except Exception:
                    pass
                break
        try:
            self.after(150, self._poll)
        except Exception:
            pass

    # ── UI 골격 ─────────────────────────────────────────────
    def _build(self):
        c = self._tc()
        hdr = tk.Frame(self, bg=c, pady=10); hdr.pack(fill="x")
        tk.Label(hdr, text="📊  급식 칼로리 분석",
                 font=("맑은 고딕",13,"bold"), fg="white", bg=c).pack()
        tk.Label(hdr, text=f"{self._school['name']}  ({self._sd()})",
                 font=("맑은 고딕",10), fg="white", bg=c).pack(pady=(2,0))

        msh = tk.Frame(self, bg="#ECEFF1", pady=4); msh.pack(fill="x")
        tk.Label(msh, text="📅  월별 분석", font=("맑은 고딕",10,"bold"),
                 bg="#ECEFF1", fg="#455A64").pack(side="left", padx=10)
        mnav = tk.Frame(self, bg=self.BG, pady=3); mnav.pack(fill="x", padx=10)
        tk.Button(mnav, text="◀ 이전달", font=("맑은 고딕",9,"bold"),
                  relief="flat", bd=0, cursor="hand2", bg="#CFD8DC", fg="#37474F",
                  padx=8, pady=2, command=self._prev_month).pack(side="left")
        self._m_title = tk.StringVar()
        tk.Label(mnav, textvariable=self._m_title,
                 font=("맑은 고딕",11,"bold"), bg=self.BG, fg="#37474F",
                 width=16, anchor="center").pack(side="left", expand=True)
        tk.Button(mnav, text="다음달 ▶", font=("맑은 고딕",9,"bold"),
                  relief="flat", bd=0, cursor="hand2", bg="#CFD8DC", fg="#37474F",
                  padx=8, pady=2, command=self._next_month).pack(side="right")
        self._upd_mt()
        self._mf = tk.Frame(self, bg=self.BG); self._mf.pack(fill="x", padx=10, pady=(0,4))

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10, pady=(4,0))

        wsh = tk.Frame(self, bg="#ECEFF1", pady=4); wsh.pack(fill="x")
        tk.Label(wsh, text="📆  주별 분석 (월~금)", font=("맑은 고딕",10,"bold"),
                 bg="#ECEFF1", fg="#455A64").pack(side="left", padx=10)
        wnav = tk.Frame(self, bg=self.BG, pady=3); wnav.pack(fill="x", padx=10)
        tk.Button(wnav, text="◀ 이전주", font=("맑은 고딕",9,"bold"),
                  relief="flat", bd=0, cursor="hand2", bg="#CFD8DC", fg="#37474F",
                  padx=8, pady=2, command=self._prev_week).pack(side="left")
        self._w_title = tk.StringVar()
        tk.Label(wnav, textvariable=self._w_title,
                 font=("맑은 고딕",11,"bold"), bg=self.BG, fg="#37474F",
                 width=20, anchor="center").pack(side="left", expand=True)
        tk.Button(wnav, text="다음주 ▶", font=("맑은 고딕",9,"bold"),
                  relief="flat", bd=0, cursor="hand2", bg="#CFD8DC", fg="#37474F",
                  padx=8, pady=2, command=self._next_week).pack(side="right")
        self._upd_wt()
        self._wf = tk.Frame(self, bg=self.BG); self._wf.pack(fill="x", padx=10, pady=(0,4))

        rl = RECOMMENDED_LUNCH_KCAL.get(self._stype,650)
        rd = RECOMMENDED_DAILY_KCAL.get(self._stype,2300)
        tk.Label(self,
                 text=f"점심 권장 {rl} kcal  /  1일(조+중+석) 권장 {rd} kcal  (±15% 적정)",
                 font=("맑은 고딕",8), bg=self.BG, fg="#AAAAAA").pack(pady=(4,0))
        tk.Button(self, text="닫기", font=("맑은 고딕",11), bg="#BBBBBB", fg="white",
                  relief="flat", cursor="hand2", bd=0, padx=20, pady=6,
                  command=self.destroy).pack(pady=(8,12))

    # ── 네비게이션 ───────────────────────────────────────────
    def _prev_month(self):
        m = self._m_month - 1
        self._m_year, self._m_month = (self._m_year-1,12) if m==0 else (self._m_year,m)
        self._upd_mt(); self._load_month()
    def _next_month(self):
        m = self._m_month + 1
        self._m_year, self._m_month = (self._m_year+1,1) if m==13 else (self._m_year,m)
        self._upd_mt(); self._load_month()
    def _prev_week(self):
        self._w_monday -= timedelta(weeks=1); self._upd_wt(); self._load_week_only()
    def _next_week(self):
        self._w_monday += timedelta(weeks=1); self._upd_wt(); self._load_week_only()

    def _upd_mt(self): self._m_title.set(f"{self._m_year}년 {self._m_month}월")
    def _upd_wt(self):
        mon = self._w_monday; fri = mon + timedelta(days=4)
        wn  = _week_number_in_month(mon)
        self._w_title.set(
            f"{mon.month}월 {wn}주차  ({mon.strftime('%m/%d')}~{fri.strftime('%m/%d')})"
        )

    # ── 로딩 ─────────────────────────────────────────────────
    def _load_both(self):
        """최초 로딩: 월 fetch → _poll에서 월+주 동시 렌더."""
        self._clr(self._mf); self._ldg(self._mf)
        self._clr(self._wf); self._ldg(self._wf)
        # 스냅샷으로 캡처
        yr, mo = self._m_year, self._m_month
        w_snap = self._w_monday
        threading.Thread(
            target=self._thr_month_then_week,
            args=(yr, mo, w_snap), daemon=True
        ).start()

    def _load_month(self):
        """이전달/다음달: 월 fetch → 주는 새 월에서 추출."""
        self._clr(self._mf); self._ldg(self._mf)
        self._clr(self._wf); self._ldg(self._wf)
        yr, mo = self._m_year, self._m_month
        w_snap = self._w_monday
        threading.Thread(
            target=self._thr_month_then_week,
            args=(yr, mo, w_snap), daemon=True
        ).start()

    def _load_week_only(self):
        """이전주/다음주: 캐시에 있으면 즉시, 없으면 fetch."""
        self._clr(self._wf); self._ldg(self._wf)
        w_snap = self._w_monday
        fri = w_snap + timedelta(days=4)
        # 이 주가 현재 캐시된 달 안에 있는지 확인
        cached = self._find_in_cache(w_snap, fri)
        if cached is not None:
            self._do_render_week(cached, None, w_snap)
        else:
            # 이 주가 속한 달을 fetch
            threading.Thread(
                target=self._thr_week_standalone,
                args=(w_snap,), daemon=True
            ).start()

    def _find_in_cache(self, mon, fri):
        """mon~fri 주간 데이터가 캐시에 있으면 추출, 없으면 None.
        달 경계에 걸친 주(예: 3/30~4/3)는 양쪽 달 캐시 모두 확인."""
        days_list = [mon + timedelta(days=i) for i in range(5)]
        months_needed = set((d.year, d.month) for d in days_list)
        # 필요한 달 캐시가 모두 있어야 함
        if not all(k in self._m_cache for k in months_needed):
            return None
        result = {}
        for day in days_list:
            d   = day.strftime("%Y%m%d")
            key = (day.year, day.month)
            if d in self._m_cache[key]:
                result[d] = self._m_cache[key][d]
        return result

    # ── 백그라운드 스레드 ─────────────────────────────────────
    def _thr_month_then_week(self, year, month, w_snap):
        """월 전체 fetch (페이지네이션) → 큐에 month 메시지 push."""
        import calendar as _c
        ld   = _c.monthrange(year, month)[1]
        f    = f"{year}{month:02d}01"
        t    = f"{year}{month:02d}{ld:02d}"
        data, err = _fetch_all_pages(f, t, self._oc, self._sc)
        if err is None and data is not None:
            self._m_cache[(year, month)] = data
        self._q.put(("month", data, err, year, month, w_snap))

    def _thr_week_standalone(self, w_snap):
        """단독 주간 fetch → 큐에 week 메시지 push.
        달 경계에 걸친 주(예: 3/30~4/3)는 양쪽 달을 모두 fetch."""
        import calendar as _c
        # 이 주에 포함된 달을 모두 파악
        months_needed = {}
        for i in range(5):
            day = w_snap + timedelta(days=i)
            key = (day.year, day.month)
            if key not in months_needed:
                months_needed[key] = day
        all_data = {}
        last_err = None
        for (yr, mo) in sorted(months_needed):
            # 이미 캐시에 있으면 재사용
            if (yr, mo) in self._m_cache:
                all_data.update(self._m_cache[(yr, mo)])
                continue
            ld  = _c.monthrange(yr, mo)[1]
            f   = f"{yr}{mo:02d}01"
            t   = f"{yr}{mo:02d}{ld:02d}"
            data, err = _fetch_all_pages(f, t, self._oc, self._sc)
            if err is None and data is not None:
                self._m_cache[(yr, mo)] = data
                all_data.update(data)
            elif err:
                last_err = err
        # 주 데이터 추출 (5일 모두)
        week_data = {}
        for i in range(5):
            d = (w_snap + timedelta(days=i)).strftime("%Y%m%d")
            if d in all_data:
                week_data[d] = all_data[d]
        self._q.put(("week", week_data, last_err, w_snap))

    # ── 렌더링 (메인 스레드에서만 호출) ─────────────────────
    def _do_render_month(self, data, err, yr, mo, w_snap):
        self._clr(self._mf)
        if err:
            tk.Label(self._mf, text=f"❌ {err}",
                     font=("맑은 고딕",10), bg=self.BG, fg="#C62828").pack(anchor="w"); return
        import calendar as _c
        ld  = _c.monthrange(yr, mo)[1]
        dr  = f"{mo}월 1일 ~ {mo}월 {ld}일"
        days, avg, status, full = _analyze(data or {}, self._stype)
        rec  = RECOMMENDED_DAILY_KCAL.get(self._stype,2300) if full \
               else RECOMMENDED_LUNCH_KCAL.get(self._stype,650)
        info = self.STATUS_INFO.get(status, self.STATUS_INFO["데이터 없음"])
        self._draw(self._mf,
            f"{dr}   급식일수 {days}일",
            f"{mo}월 우리 {self._sd()}의 에너지",
            days, avg, rec, status, info, full)
        # 주 렌더 (month fetch 완료 후 즉시, 달 경계 주간도 처리)
        self._clr(self._wf)
        if w_snap is not None:
            week_data = {}
            for i in range(5):
                day = w_snap + timedelta(days=i)
                d   = day.strftime("%Y%m%d")
                key = (day.year, day.month)
                # 현재 달 데이터 또는 캐시에서 조회
                src_data = data if key == (yr, mo) else self._m_cache.get(key, {})
                if d in src_data:
                    week_data[d] = src_data[d]
            # 달 경계 주간이면 다른 달 데이터가 캐시에 없을 수 있음 → 백그라운드 보완
            missing = [i for i in range(5)
                       if (w_snap + timedelta(days=i)).strftime("%Y%m%d") not in week_data
                       and (w_snap + timedelta(days=i)).month != mo]
            if missing:
                threading.Thread(
                    target=self._thr_week_standalone,
                    args=(w_snap,), daemon=True
                ).start()
            else:
                self._do_render_week(week_data, None, w_snap)

    def _do_render_week(self, data, err, w_snap):
        self._clr(self._wf)
        if err:
            tk.Label(self._wf, text=f"❌ {err}",
                     font=("맑은 고딕",10), bg=self.BG, fg="#C62828").pack(anchor="w"); return
        fri = w_snap + timedelta(days=4)
        wn  = _week_number_in_month(w_snap)
        DAY = ["월","화","수","목","금","토","일"]
        dr  = (f"{w_snap.strftime('%m/%d')}({DAY[w_snap.weekday()]})"
               f" ~ {fri.strftime('%m/%d')}({DAY[fri.weekday()]})")
        days, avg, status, full = _analyze(data or {}, self._stype)
        rec  = RECOMMENDED_DAILY_KCAL.get(self._stype,2300) if full \
               else RECOMMENDED_LUNCH_KCAL.get(self._stype,650)
        info = self.STATUS_INFO.get(status, self.STATUS_INFO["데이터 없음"])
        self._draw(self._wf,
            f"{dr}   급식일수 {days}일",
            f"{w_snap.month}월 {wn}주차 우리 {self._sd()}의 에너지",
            days, avg, rec, status, info, full)
        # w_title도 현재 w_snap 기준으로 갱신
        self._w_monday = w_snap
        self._upd_wt()

    def _draw(self, parent, header, verdict, days, avg, rec, status, info, full):
        color, bg = info["color"], info["bg"]
        tk.Label(parent, text=header,
                 font=("맑은 고딕",9,"bold"), bg=self.BG, fg="#555555"
                 ).pack(anchor="w", pady=(4,2))
        if days == 0 or avg == 0:
            row = tk.Frame(parent, bg=self.BG); row.pack(anchor="w", pady=2)
            _MinisBap(row, bg=self.BG, face="normal", color="#9E9E9E").pack(side="left")
            tk.Label(row, text=f"  {info['icon']}  {status}",
                     font=("맑은 고딕",14,"bold"), bg=self.BG, fg="#9E9E9E").pack(side="left")
            return
        card = tk.Frame(parent, bg=bg, highlightbackground=color, highlightthickness=1)
        card.pack(fill="x", pady=(0,4), ipady=3)
        lf = tk.Frame(card, bg=bg); lf.pack(side="left", padx=10, pady=4)
        note = "조+중+석" if full else "점심"
        tk.Label(lf, text=f"평균 칼로리 ({note})",
                 font=("맑은 고딕",8), bg=bg, fg="#777777").pack(anchor="w")
        tk.Label(lf, text=f"{avg:,.1f} kcal",
                 font=("맑은 고딕",16,"bold"), bg=bg, fg=color).pack(anchor="w")
        tk.Label(lf, text=f"권장 {rec:,} kcal",
                 font=("맑은 고딕",8), bg=bg, fg="#888888").pack(anchor="w")
        rf = tk.Frame(card, bg=bg); rf.pack(side="right", padx=10)
        tk.Label(rf, text=info["icon"], font=("Arial",24), bg=bg).pack()
        BW = 340
        fw  = int(BW * min(avg/rec, 1.5) / 1.5)
        lx  = int(BW * 0.85 / 1.5); hx = int(BW * 1.15 / 1.5)
        bc  = tk.Canvas(parent, width=BW, height=13, bg="#E0E0E0", highlightthickness=0)
        bc.pack(anchor="w", pady=(0,2))
        bc.create_rectangle(0, 0, fw, 13, fill=color, outline="")
        bc.create_rectangle(lx, 0, hx, 13, fill="#A5D6A7", outline="", stipple="gray50")
        bc.create_text(BW//2, 6,
                       text=f"적정 {int(rec*0.85)}~{int(rec*1.15)} kcal",
                       font=("맑은 고딕",7), fill="#555555")
        row = tk.Frame(parent, bg=self.BG); row.pack(anchor="w")
        _MinisBap(row, bg=self.BG, face=info["face"], color=color).pack(side="left")
        vf = tk.Frame(row, bg=self.BG); vf.pack(side="left", padx=6)
        tk.Label(vf, text=verdict,
                 font=("맑은 고딕",10), bg=self.BG, fg="#555555").pack(anchor="w")
        tk.Label(vf, text=f"{info['icon']}  {status}",
                 font=("맑은 고딕",17,"bold"), bg=self.BG, fg=color).pack(anchor="w")
        pct = (avg/rec-1)*100; sign = "+" if pct>=0 else ""
        tk.Label(vf, text=f"권장 대비 {sign}{pct:.1f}%  ({avg:.0f} / {rec} kcal)",
                 font=("맑은 고딕",8), bg=self.BG, fg="#888888").pack(anchor="w")


# ─── 분석 전용 헬퍼 ──────────────────────────────────────────────
RECOMMENDED_DAILY_KCAL = {
    "유치원":   1400,
    "초등학교": 1700,
    "중학교":   2250,
    "고등학교": 2350,
    "특수학교": 1950,
    "기관":     2300,
}

def _fetch_all_pages(from_ymd, to_ymd, office_code, school_code):
    """
    기간 내 모든 급식 데이터를 수집.
    - API키 있음: 페이지네이션으로 한번에 수집
    - API키 없음: NEIS가 5건 제한을 걸므로 날짜별 1건씩 개별 호출
    Returns ({ymd:{mc:kcal}}, err|None)
    """
    def _parse_rows(rows, result):
        for row in rows:
            ymd = row.get("MLSV_YMD","")
            if not ymd: continue
            mc  = int(row.get("MMEAL_SC_CODE", 2))
            try:
                v = float(re.search(r"[\d.]+", row.get("CAL_INFO","").strip()).group())
            except Exception:
                continue
            if ymd not in result:
                result[ymd] = {}
            result[ymd][mc] = v

    result = {}

    if API_KEY:
        # ── API키 있음: 페이지네이션 ──
        page = 1
        PAGE_SIZE = 100
        while True:
            url = (
                "https://open.neis.go.kr/hub/mealServiceDietInfo"
                f"?Type=json&pIndex={page}&pSize={PAGE_SIZE}"
                f"&KEY={API_KEY}"
                f"&ATPT_OFCDC_SC_CODE={office_code}"
                f"&SD_SCHUL_CODE={school_code}"
                f"&MLSV_FROM_YMD={from_ymd}"
                f"&MLSV_TO_YMD={to_ymd}"
            )
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                return None, f"네트워크 오류: {e}"
            if "mealServiceDietInfo" not in data:
                code = data.get("RESULT",{}).get("CODE","")
                if code == "INFO-200": break
                return None, data.get("RESULT",{}).get("MESSAGE","API 오류")
            rows = data["mealServiceDietInfo"][1].get("row", [])
            _parse_rows(rows, result)
            if len(rows) < PAGE_SIZE: break
            page += 1
    else:
        # ── API키 없음: 날짜별 1건씩 개별 호출 (5건 제한 우회) ──
        from datetime import datetime as _dt, timedelta as _td
        try:
            cur = _dt.strptime(from_ymd, "%Y%m%d")
            end = _dt.strptime(to_ymd,   "%Y%m%d")
        except Exception as e:
            return None, f"날짜 파싱 오류: {e}"
        last_err = None
        while cur <= end:
            ymd = cur.strftime("%Y%m%d")
            url = (
                "https://open.neis.go.kr/hub/mealServiceDietInfo"
                f"?Type=json&pIndex=1&pSize=5"
                f"&ATPT_OFCDC_SC_CODE={office_code}"
                f"&SD_SCHUL_CODE={school_code}"
                f"&MLSV_YMD={ymd}"
            )
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if "mealServiceDietInfo" in data:
                    rows = data["mealServiceDietInfo"][1].get("row", [])
                    _parse_rows(rows, result)
            except Exception as e:
                last_err = str(e)
            cur += _td(days=1)
        if last_err and not result:
            return None, f"네트워크 오류: {last_err}"

    return result, None


# 하위 호환: 기존 이름으로도 호출 가능
def fetch_month_meals_all(from_ymd, to_ymd, office_code, school_code):
    return _fetch_all_pages(from_ymd, to_ymd, office_code, school_code)


def _analyze(day_data, stype):
    """Returns (meal_days, avg, status_str, full_meal_bool)
    급식 데이터(칼로리)가 있는 날을 모두 집계.
    중식 코드(2)가 없어도 해당 날에 등록된 칼로리를 사용."""
    if not day_data: return 0, 0.0, "데이터 없음", False
    full_days = sum(1 for m in day_data.values() if 1 in m or 3 in m)
    full = (stype in ("중학교","고등학교","특수학교")) and \
           (full_days >= len(day_data) * 0.5)
    totals = []
    for meals in day_data.values():
        if not meals:
            continue  # 칼로리 데이터 없는 날 스킵
        if full:
            v = sum(meals.values())
        else:
            # 중식(2) 우선, 없으면 그 날 등록된 다른 급식 칼로리 사용
            v = meals.get(2, 0)
            if v == 0:
                v = next(iter(meals.values()), 0)
        if v > 0:
            totals.append(v)
    if not totals: return 0, 0.0, "데이터 없음", full
    avg = sum(totals) / len(totals)
    rec = RECOMMENDED_DAILY_KCAL.get(stype, 2300) if full \
          else RECOMMENDED_LUNCH_KCAL.get(stype, 650)
    return len(totals), avg, _judge(avg, rec), full


class _MinisBap(tk.Canvas):
    """팝업 안 소형 밥풀이."""
    W, H = 80, 95
    def __init__(self, master, bg="#FAFAFA", face="normal", color="#66BB6A"):
        super().__init__(master, width=self.W, height=self.H, bg=bg, highlightthickness=0)
        cx, cy = self.W//2, 60
        self.create_oval(cx-18,cy+22,cx+18,cy+27,fill="#C8C8C8",outline="",stipple="gray50")
        self.create_arc(cx-22,cy+8,cx+22,cy+28,start=0,extent=-180,
                        fill="#DEC895",outline="#B89A58",width=1,style="chord")
        self.create_arc(cx-20,cy-2,cx+20,cy+18,start=180,extent=180,
                        fill="#F2E4C0",outline="#B89A58",width=1,style="chord")
        self.create_oval(cx-17,cy-16,cx+17,cy+8,fill="#FFFEFA",outline="#EAE0CC",width=1)
        self.create_oval(cx-6,cy-16,cx+6,cy-9,fill=color,outline="",stipple="gray50")
        fy = cy-24
        self.create_oval(cx-13,fy+3,cx-7,fy+7,fill="#FFB3BA",outline="",stipple="gray75")
        self.create_oval(cx+7,fy+3,cx+13,fy+7,fill="#FFB3BA",outline="",stipple="gray75")
        if face=="angry":
            self.create_arc(cx-10,fy+2,cx-4,fy+7,start=180,extent=180,
                            fill="#3A3A3A",outline="",style="chord")
            self.create_arc(cx+4,fy+2,cx+10,fy+7,start=180,extent=180,
                            fill="#3A3A3A",outline="",style="chord")
        else:
            self.create_arc(cx-10,fy,cx-4,fy+5,start=0,extent=180,
                            fill="#3A3A3A",outline="",style="chord")
            self.create_arc(cx+4,fy,cx+10,fy+5,start=0,extent=180,
                            fill="#3A3A3A",outline="",style="chord")
        self.create_oval(cx-9,fy+1,cx-7,fy+2,fill="white",outline="")
        self.create_oval(cx+6,fy+1,cx+8,fy+2,fill="white",outline="")
        if face=="sad":
            self.create_arc(cx-5,fy+7,cx+5,fy+13,start=20,extent=140,
                            fill="",outline="#3A3A3A",width=1)
        else:
            self.create_arc(cx-5,fy+5,cx+5,fy+11,start=200,extent=140,
                            fill="",outline="#3A3A3A",width=1)
        self.create_oval(cx-24,cy,cx-16,cy+8,fill="#FFFEFA",outline="#E0D8C0",width=1)
        self.create_oval(cx+16,cy,cx+24,cy+8,fill="#FFFEFA",outline="#E0D8C0",width=1)



class SettingsDialog(tk.Toplevel):
    BG    = "#F5FAF4"
    POINT = "#66BB6A"
    GRAY  = "#7A9A7E"

    TAB_TYPES  = ["유치원", "초등학교", "중학교", "고등학교", "특수학교", "기관"]
    TAB_COLORS = {
        "유치원":"#F48FB1","초등학교":"#66BB6A",
        "중학교":"#42A5F5","고등학교":"#AB47BC","특수학교":"#78909C","기관":"#FF8A65"
    }
    TAB_ICONS  = {
        "유치원":"🌸","초등학교":"🌿","중학교":"📘","고등학교":"🎓","특수학교":"🏥","기관":"🏛️"
    }

    OFFICE_DISPLAY      = ["전체"] + [v["name"] for v in OFFICE_INFO.values()]
    OFFICE_CODE_BY_NAME = {"전체": "전체",
                            **{v["name"]: k for k, v in OFFICE_INFO.items()}}
    OFFICE_NAME_BY_CODE = {"전체": "전체",
                            **{k: v["name"] for k, v in OFFICE_INFO.items()}}

    def __init__(self, parent, current_school: dict, on_save):
        super().__init__(parent)
        self.title("⚙️ 설정")
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg=self.BG)
        self._current        = current_school
        self._on_save        = on_save
        self._selected       = current_school.copy()
        self._active_office  = current_school.get("office", "전체")
        self._active_tab     = current_school.get("type", "초등학교")
        if self._active_tab not in self.TAB_TYPES:
            self._active_tab = "초등학교"
        self._filtered       = {}
        self._build()
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _schools_for_type(self, tab_type):
        return SCHOOL_BY_OFFICE_TYPE.get((self._active_office, tab_type), [])

    def _build(self):
        hdr = tk.Frame(self, bg=self.POINT, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚙️  기본 학교 설정",
                 font=("맑은 고딕", 14, "bold"),
                 fg="white", bg=self.POINT).pack()

        tk.Label(self, text="프로그램 시작 시 기본으로 표시할 학교를 선택하세요.",
                 font=("맑은 고딕", 10), bg=self.BG, fg=self.GRAY,
                 wraplength=320).pack(pady=(12, 4), padx=16)

        self._sel_var = tk.StringVar(value=f"📌 {self._selected['name']}")
        tk.Label(self, textvariable=self._sel_var,
                 font=("맑은 고딕", 11, "bold"),
                 bg="#E8F5E9", fg="#2E7D32",
                 padx=10, pady=6).pack(fill="x", padx=16, pady=(0, 8))

        # 교육청 선택
        oc_frame = tk.Frame(self, bg="#E8F5E9", pady=5)
        oc_frame.pack(fill="x", padx=0)
        tk.Label(oc_frame, text="🏢 교육청",
                 font=("맑은 고딕", 10, "bold"),
                 bg="#E8F5E9", fg="#2E7D32").pack(side="left", padx=(12, 6))
        self._office_var = tk.StringVar(
            value=self.OFFICE_NAME_BY_CODE.get(self._active_office, "전체"))
        self._office_cb = ttk.Combobox(
            oc_frame, textvariable=self._office_var,
            values=self.OFFICE_DISPLAY,
            font=("맑은 고딕", 10), state="readonly", width=22)
        self._office_cb.pack(side="left", padx=(0, 12))
        self._office_cb.bind("<<ComboboxSelected>>", self._on_office_change)

        # 탭
        tab_frame = tk.Frame(self, bg="#DCF0DC")
        tab_frame.pack(fill="x")
        self._tab_btns = {}
        for t in self.TAB_TYPES:
            color = self.TAB_COLORS[t]
            icon  = self.TAB_ICONS[t]
            cnt   = len(self._schools_for_type(t))
            btn   = tk.Button(tab_frame,
                              text=f"{icon}\n{t}({cnt})",
                              font=("맑은 고딕", 8, "bold"),
                              relief="flat", bd=0, cursor="hand2",
                              padx=4, pady=5,
                              command=lambda tt=t: self._switch_tab(tt))
            btn.pack(side="left", fill="x", expand=True)
            self._tab_btns[t] = (btn, color)
        self._refresh_tabs()

        # 검색
        sf = tk.Frame(self, bg=self.BG, pady=6)
        sf.pack(fill="x", padx=14)
        tk.Label(sf, text="🔍", bg=self.BG).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())
        tk.Entry(sf, textvariable=self._search_var,
                 font=("맑은 고딕", 11), relief="flat",
                 bg="white", highlightbackground="#CCDDCC", highlightthickness=1
                 ).pack(side="left", fill="x", expand=True, padx=(4, 0), ipady=3)

        # 리스트
        lf = tk.Frame(self, bg=self.BG)
        lf.pack(fill="both", expand=True, padx=14, pady=(0, 4))
        sb = ttk.Scrollbar(lf, orient="vertical")
        self._listbox = tk.Listbox(lf,
            font=("맑은 고딕", 11), height=14, width=26,
            selectbackground=self.POINT, selectforeground="white",
            activestyle="none", relief="flat", bd=0,
            highlightthickness=1, highlightbackground="#CCDDCC",
            yscrollcommand=sb.set, cursor="hand2")
        sb.config(command=self._listbox.yview)
        self._listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._listbox.bind("<Double-Button-1>", lambda e: self._pick())
        self._refresh_list()

        # 버튼
        br = tk.Frame(self, bg=self.BG, pady=8)
        br.pack(fill="x", padx=14)
        self._save_btn = tk.Button(br, text="💾  기본학교로 저장",
                  font=("맑은 고딕", 11, "bold"),
                  bg=self.POINT, fg="white", relief="flat",
                  padx=12, pady=6, cursor="hand2", bd=0,
                  command=self._save)
        self._save_btn.pack(side="left", fill="x", expand=True)
        tk.Frame(br, bg=self.BG, width=8).pack(side="left")
        tk.Button(br, text="취소",
                  font=("맑은 고딕", 11),
                  bg="#BBBBBB", fg="white", relief="flat",
                  padx=12, pady=6, cursor="hand2", bd=0,
                  command=self.destroy).pack(side="left", fill="x", expand=True)

    def _on_office_change(self, _=None):
        name = self._office_var.get()
        self._active_office = self.OFFICE_CODE_BY_NAME.get(name, "전체")
        self._filtered = {}
        self._search_var.set("")
        self._refresh_tabs()
        self._refresh_list()

    def _refresh_tabs(self):
        for t, (btn, color) in self._tab_btns.items():
            cnt  = len(self._schools_for_type(t))
            icon = self.TAB_ICONS[t]
            text = f"{icon}\n{t}({cnt})"
            if t == self._active_tab:
                btn.configure(bg=color, fg="white", text=text)
            else:
                btn.configure(bg="#DCF0DC", fg="#557755", text=text)

    def _switch_tab(self, tab_type):
        self._active_tab = tab_type
        self._search_var.set("")
        self._filtered[tab_type] = self._schools_for_type(tab_type)[:]
        color = self.TAB_COLORS.get(tab_type, self.POINT)
        self._listbox.configure(selectbackground=color)
        self._save_btn.configure(bg=color)
        self._refresh_tabs()
        self._refresh_list()

    def _on_search(self):
        q = self._search_var.get().strip()
        t = self._active_tab
        base = self._schools_for_type(t)
        self._filtered[t] = [s for s in base if q in s["name"]] if q else base[:]
        self._refresh_list()

    def _refresh_list(self):
        self._listbox.delete(0, "end")
        t = self._active_tab
        if t not in self._filtered:
            self._filtered[t] = self._schools_for_type(t)[:]
        lst = self._filtered[t]
        sel_idx = None
        for i, s in enumerate(lst):
            self._listbox.insert("end", f"  {s['name']}")
            if s["code"] == self._selected.get("code"):
                sel_idx = i
        if sel_idx is not None:
            self._listbox.selection_set(sel_idx)
            self._listbox.see(sel_idx)

    def _pick(self):
        idxs = self._listbox.curselection()
        if not idxs: return
        s = self._filtered[self._active_tab][idxs[0]]
        self._selected = s
        self._sel_var.set(f"📌 {s['name']}")

    def _save(self):
        idxs = self._listbox.curselection()
        if idxs:
            self._selected = self._filtered[self._active_tab][idxs[0]]
        self._on_save(self._selected)
        self.destroy()


# ─── 메인 앱 ─────────────────────────────────────────────────
class MealApp(tk.Tk):
    BG   = "#F0F7EE"
    CARD = "#FFFFFF"
    GRAY = "#8A9B8E"
    TEXT = "#2C3A2E"

    TYPE_COLORS = {
        "유치원":   "#F48FB1",
        "초등학교": "#66BB6A",
        "중학교":   "#42A5F5",
        "고등학교": "#AB47BC",
        "특수학교": "#78909C",
        "기관":     "#FF8A65",
    }
    TYPE_BG = {
        "유치원":   "#FDF0F5",
        "초등학교": "#F0F7EE",
        "중학교":   "#EEF5FD",
        "고등학교": "#F5EEF8",
        "특수학교": "#ECEFF1",
        "기관":     "#FFF3EE",
    }
    TYPE_NAV_BG = {
        "유치원":   "#F8BBD9",
        "초등학교": "#C8E6C9",
        "중학교":   "#BBDEFB",
        "고등학교": "#E1BEE7",
        "특수학교": "#CFD8DC",
        "기관":     "#FFCCBC",
    }
    TYPE_ICONS = {
        "유치원":"🌸","초등학교":"🌿","중학교":"📘","고등학교":"🎓","특수학교":"🏥","기관":"🏛️"
    }

    def __init__(self):
        super().__init__()
        self.configure(bg=self.BG)
        self.resizable(False, False)
        self._center(520, 800)
        self.today     = datetime.today().replace(hour=0,minute=0,second=0,microsecond=0)
        self.cur_date  = self.today
        self._week_win = None

        # ── 설정에서 기본 학교 불러오기 ──
        cfg = load_settings()
        saved = cfg.get("default_school")
        if saved and isinstance(saved, dict) and "code" in saved:
            found = next((s for s in SCHOOL_LIST if s["code"] == saved["code"]), None)
            self._school = found.copy() if found else DEFAULT_SCHOOL.copy()
        else:
            self._school = DEFAULT_SCHOOL.copy()

        self._build_ui()
        self._badge_frame    = None
        self._badge_anim_id  = None
        self._badge_visible  = False
        self._badge_btns     = []
        self.after(100, self.load_meal)

    def _center(self, w, h):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _color(self):
        return self.TYPE_COLORS.get(self._school.get("type","초등학교"), "#66BB6A")

    def _bg_color(self):
        return self.TYPE_BG.get(self._school.get("type","초등학교"), self.BG)

    def _nav_bg(self):
        return self.TYPE_NAV_BG.get(self._school.get("type","초등학교"), "#C8E6C9")

    # ── UI 구성 ─────────────────────────────────────────────
    def _build_ui(self):
        # ① 헤더 (학교명 + 설정 톱니바퀴)
        self._hdr_frame = tk.Frame(self, bg=self._color(), pady=10)
        self._hdr_frame.pack(fill="x")

        hdr_inner = tk.Frame(self._hdr_frame, bg=self._color())
        hdr_inner.pack(fill="x", padx=12)

        # 학교명 버튼 (클릭 → 다른학교보기)
        self._school_var = tk.StringVar()
        self._school_btn = tk.Button(
            hdr_inner, textvariable=self._school_var,
            font=("맑은 고딕", 15, "bold"),
            bg=self._color(), fg="white", relief="flat", cursor="hand2", bd=0,
            activebackground=self._color(), activeforeground="#F0F0F0",
            command=self._open_other_schools)
        self._school_btn.pack(side="left")

        tk.Label(hdr_inner, text="▼", font=("맑은 고딕", 10),
                 bg=self._color(), fg="white").pack(side="left")

        # BY LEE YANG-HO 크레딧
        self._credit_lbl = tk.Label(
            hdr_inner, text="BY LEE YANG-HO",
            font=("맑은 고딕", 7), bg=self._color(), fg="#DDDDDD"
        )
        self._credit_lbl.pack(side="left", padx=(8, 0))

        # 설정 톱니바퀴 버튼 (오른쪽)
        self._gear_btn = tk.Button(
            hdr_inner, text="⚙️",
            font=("Arial", 16), bg=self._color(), fg="white",
            relief="flat", cursor="hand2", bd=0,
            activebackground=self._color(),
            command=self._open_settings)
        self._gear_btn.pack(side="right", padx=(0, 2))

        # 다른학교보기 작은 버튼
        self._other_btn = tk.Button(
            hdr_inner, text="다른학교보기",
            font=("맑은 고딕", 8), bg="white", fg=self._color(),
            relief="flat", cursor="hand2", bd=0, padx=8, pady=3,
            command=self._open_other_schools)
        self._other_btn.pack(side="right", padx=4)

        # ② 날짜 내비게이션
        self._nav_frame = tk.Frame(self, bg=self._nav_bg(), pady=6)
        self._nav_frame.pack(fill="x")

        self._nav_prev = tk.Button(self._nav_frame, text="◀ 어제",
                  font=("맑은 고딕", 10, "bold"),
                  bg=self._color(), fg="white",
                  relief="flat", padx=10, pady=4, cursor="hand2", bd=0,
                  command=self.prev_day)
        self._nav_prev.pack(side="left", padx=(10, 0))

        self._nav_next = tk.Button(self._nav_frame, text="내일 ▶",
                  font=("맑은 고딕", 10, "bold"),
                  bg=self._color(), fg="white",
                  relief="flat", padx=10, pady=4, cursor="hand2", bd=0,
                  command=self.next_day)
        self._nav_next.pack(side="right", padx=(0, 10))

        self._nav_today = tk.Button(self._nav_frame, text="오늘",
                  font=("맑은 고딕", 10),
                  bg="#A5C8A0", fg="white",
                  relief="flat", padx=8, pady=4, cursor="hand2", bd=0,
                  command=self.go_today)
        self._nav_today.pack(side="right", padx=4)

        self.date_var = tk.StringVar()
        self._update_date_label()
        self._date_btn = tk.Button(self._nav_frame, textvariable=self.date_var,
                  font=("맑은 고딕", 11, "bold"),
                  bg=self._nav_bg(), fg=self.TEXT,
                  relief="flat", cursor="hand2", bd=0,
                  activebackground=self._nav_bg(),
                  command=self.open_date_picker)
        self._date_btn.pack(side="left", expand=True)
        self._cal_lbl = tk.Label(self._nav_frame, text="📅",
                 font=("Arial", 11), bg=self._nav_bg())
        self._cal_lbl.pack(side="left")

        # ③ 버튼 행
        btn_row = tk.Frame(self, bg=self._bg_color())
        btn_row.pack(fill="x", padx=14, pady=(10, 4))
        self._search_btn = tk.Button(btn_row, text="🔍  점심 급식 조회",
                  font=("맑은 고딕", 12, "bold"),
                  bg=self._color(), fg="white", relief="flat",
                  pady=9, cursor="hand2", bd=0,
                  command=self.load_meal)
        self._search_btn.pack(side="left", fill="x", expand=True)
        tk.Frame(btn_row, bg=self._bg_color(), width=8).pack(side="left")
        self._week_btn = tk.Button(btn_row, text="📋  한주 보기",
                  font=("맑은 고딕", 12, "bold"),
                  bg="#78C9C0", fg="white", relief="flat",
                  pady=9, cursor="hand2", bd=0,
                  command=self.open_week_view)
        self._week_btn.pack(side="left", fill="x", expand=True)
        self._btn_row = btn_row

        # 상태
        self.status_var = tk.StringVar(value="")
        self._status_lbl = tk.Label(self, textvariable=self.status_var,
                 font=("맑은 고딕", 10), bg=self._bg_color(), fg=self.GRAY)
        self._status_lbl.pack(pady=(0, 2))

        # ④ 결과 영역 (Canvas + 오버레이용 Frame)
        self._result_outer = tk.Frame(self, bg=self._bg_color())
        self._result_outer.pack(fill="both", expand=True, padx=14, pady=0)

        self._canvas = tk.Canvas(self._result_outer, bg=self._bg_color(),
                                  highlightthickness=0)
        self._sb = ttk.Scrollbar(self._result_outer, orient="vertical",
                                  command=self._canvas.yview)
        self.meal_frame = tk.Frame(self._canvas, bg=self._bg_color())
        self.meal_frame.bind("<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.create_window((0,0), window=self.meal_frame, anchor="nw")
        self._canvas.configure(yscrollcommand=self._sb.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        self._sb.pack(side="right", fill="y")
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))

        # 밥풀이 오버레이 캐릭터 (result_outer 위에 place로 띄울 것)
        self._bap = BapPuri(self._result_outer, bg=self._bg_color(),
                            on_click=self._show_monthly_report)

        # ⑤ 하단
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=14, pady=(4,0))
        bottom = tk.Frame(self, bg=self._bg_color(), pady=5)
        bottom.pack(fill="x", padx=14)
        self._startup_var = tk.StringVar()
        self._startup_btn = tk.Button(bottom, textvariable=self._startup_var,
            font=("맑은 고딕", 9), relief="flat", cursor="hand2", bd=0,
            padx=10, pady=4, command=self._toggle_startup)
        self._startup_btn.pack(side="left")
        self._refresh_startup_btn()
        tk.Label(self, text="NEIS 학교급식 공개 API 제공",
                 font=("맑은 고딕", 8), bg=self._bg_color(), fg=self.GRAY).pack(pady=(0,4))

        self._refresh_school_ui()

    # ── UI 색상 갱신 ─────────────────────────────────────────
    def _refresh_school_ui(self):
        name  = self._school["name"]
        color = self._color()
        nbg   = self._nav_bg()
        bg_c  = self._bg_color()

        self._school_var.set(f" {name} ")
        self.title(f"{name} 급식 알리미")

        # 헤더
        self._hdr_frame.configure(bg=color)
        for w in self._hdr_frame.winfo_children():
            try: w.configure(bg=color)
            except Exception: pass
            if isinstance(w, tk.Frame):
                for ww in w.winfo_children():
                    try: ww.configure(bg=color)
                    except Exception: pass
        try:
            self._other_btn.configure(fg=color)
            self._school_btn.configure(bg=color, activebackground=color)
            self._gear_btn.configure(bg=color, activebackground=color)
            self._credit_lbl.configure(bg=color)
        except Exception: pass

        # 내비
        self._nav_frame.configure(bg=nbg)
        for w in self._nav_frame.winfo_children():
            try:
                if w in (self._nav_prev, self._nav_next):
                    w.configure(bg=color)
                elif w in (self._date_btn, self._cal_lbl):
                    w.configure(bg=nbg, activebackground=nbg)
                else:
                    w.configure(bg=nbg)
            except Exception: pass

        # 버튼/배경
        self._search_btn.configure(bg=color)
        self.configure(bg=bg_c)
        for w in (self._btn_row, self._result_outer, self._canvas,
                  self.meal_frame, self._status_lbl):
            try: w.configure(bg=bg_c)
            except Exception: pass
        self._bap.configure(bg=bg_c)
        self._bap._bg = bg_c

    # ── 다른학교보기 / 설정 ────────────────────────────────
    def _open_other_schools(self):
        picker = SchoolPicker(self, self._school)
        self.wait_window(picker)
        if picker.result:
            self._school = picker.result.copy()
            self._refresh_school_ui()
            if self._week_win and self._week_win.winfo_exists():
                self._week_win.destroy()
            self.load_meal()

    def _open_settings(self):
        def on_save(school):
            # 설정에 저장
            cfg = load_settings()
            cfg["default_school"] = school
            save_settings(cfg)
            # 현재 학교도 변경
            self._school = school.copy()
            self._refresh_school_ui()
            self.load_meal()
            messagebox.showinfo("저장 완료 ✅",
                f"'{school['name']}'을(를) 기본 학교로 저장했습니다.\n"
                "다음 실행부터 이 학교가 기본으로 나타납니다.")
        SettingsDialog(self, self._school, on_save=on_save)

    def open_week_view(self):
        if self._week_win and self._week_win.winfo_exists():
            self._week_win.lift(); self._week_win.focus_force(); return
        self._week_win = WeekView(
            self, self.cur_date,
            self._school["office"],
            self._school["code"],
            self._school["name"],
            on_school_change=self._on_week_school_change,
        )

    def _on_week_school_change(self, school):
        self._school = school.copy()
        self._refresh_school_ui()
        self.load_meal()

    def _show_monthly_report(self):
        """밥풀이 클릭 시 해당 월 칼로리 분석 팝업 열기"""
        monday = self.cur_date - timedelta(days=self.cur_date.weekday())
        MonthlyKcalPopup(
            self,
            year=self.cur_date.year,
            month=self.cur_date.month,
            week_monday=monday,
            school=self._school,
            office_code=self._school["office"],
            school_code=self._school["code"],
        )

    # ── 시작프로그램 ─────────────────────────────────────────
    def _refresh_startup_btn(self):
        if is_registered():
            self._startup_var.set("✅ 시작프로그램 등록됨  (클릭 해제)")
            self._startup_btn.configure(bg="#C8E6C9", fg="#2E7D32")
        else:
            self._startup_var.set("🔔 시작프로그램 등록하기")
            self._startup_btn.configure(bg="#E8F5E9", fg="#388E3C")

    def _toggle_startup(self):
        if is_registered():
            unregister_startup()
            messagebox.showinfo("해제", "시작프로그램에서 해제되었습니다.")
        else:
            try:
                do_register()
                messagebox.showinfo("등록 완료 🎉",
                    "시작프로그램에 등록되었습니다!\n"
                    f"📁 위치: {get_startup_folder()}")
            except Exception as e:
                messagebox.showerror("등록 실패", f"{e}\n\n{get_startup_folder()}")
        self._refresh_startup_btn()

    # ── 날짜 ────────────────────────────────────────────────
    def _update_date_label(self):
        wd = ["월","화","수","목","금","토","일"][self.cur_date.weekday()]
        self.date_var.set(f" {self.cur_date.strftime(f'%Y년 %m월 %d일 ({wd})')} ")

    def prev_day(self):
        self.cur_date -= timedelta(days=1)
        self._update_date_label(); self.load_meal()

    def next_day(self):
        self.cur_date += timedelta(days=1)
        self._update_date_label(); self.load_meal()

    def go_today(self):
        self.cur_date = self.today
        self._update_date_label(); self.load_meal()

    def open_date_picker(self):
        picker = DatePicker(self, self.cur_date)
        self.wait_window(picker)
        if picker.result:
            self.cur_date = picker.result
            self._update_date_label(); self.load_meal()

    # ── 급식 조회 ───────────────────────────────────────────
    def load_meal(self):
        self.status_var.set(f"⏳ {self._school['name']} 급식 불러오는 중...")
        self._bap.hide()
        self._clear_meal_badges()
        for w in self.meal_frame.winfo_children():
            w.destroy()
        date = self.cur_date
        oc   = self._school["office"]
        sc   = self._school["code"]
        def _fetch():
            result = fetch_meal(date, oc, sc)
            self.after(0, lambda: self._render(*result))
        threading.Thread(target=_fetch, daemon=True).start()

    def _render(self, data, err):
        self.status_var.set("")
        color = self._color()
        bg_c  = self._bg_color()
        for w in self.meal_frame.winfo_children():
            w.destroy()
        self._bap.hide()
        self._clear_meal_badges()

        if err:
            self._card("❌ 오류 발생", err, "#FFEBEE", title_color="#C62828")
            return
        if not data:
            wd = ["월","화","수","목","금","토","일"][self.cur_date.weekday()]
            date_str = self.cur_date.strftime(f"%Y년 %m월 %d일 ({wd})")
            self._card("🚫 급식 없는 날",
                       f"{date_str}은\n급식을 운영하지 않는 날입니다.\n\n주말 · 방학 · 재량휴업일일 수 있어요!",
                       "#F5F5F5", title_color="#9E9E9E")
            return

        # ── 점심(2) 카드 표시 ──────────────────────────────────
        lunch = data.get(2)
        if lunch:
            self._card("🍚 점심 급식", lunch["menu"], "#FFFFFF",
                       kcal=lunch.get("kcal",""), title_color=color)
            if lunch.get("orplc"):
                orplc = lunch["orplc"].replace("<br/>","\n").replace("/","\n").strip()
                self._card("🌿 원산지 정보", orplc, "#F1F8E9")
        else:
            wd = ["월","화","수","목","금","토","일"][self.cur_date.weekday()]
            date_str = self.cur_date.strftime(f"%Y년 %m월 %d일 ({wd})")
            self._card("🚫 급식 없는 날",
                       f"{date_str}은\n급식을 운영하지 않는 날입니다.\n\n주말 · 방학 · 재량휴업일일 수 있어요!",
                       "#F5F5F5", title_color="#9E9E9E")

        # ── 아침(1)/저녁(3) 깜빡이는 뱃지 ─────────────────────
        has_breakfast = 1 in data
        has_dinner    = 3 in data
        if has_breakfast or has_dinner:
            self._show_meal_badges(data, has_breakfast, has_dinner)

        # 밥풀이 — result_outer 우측 하단에 place로 오버레이
        if lunch:
            self._result_outer.update_idletasks()
            ow = self._result_outer.winfo_width()
            oh = self._result_outer.winfo_height()
            bw, bh = BapPuri.W, BapPuri.H
            self._bap.place(x=ow - bw - 4, y=oh - bh - 4)
            m1, m2, mc = get_kcal_judge(
                lunch.get("kcal", ""),
                self._school.get("type", "초등학교")
            )
            self._bap.show(msg1=m1, msg2=m2, msg_color=mc)

    # ── 아침/저녁 뱃지 관련 ────────────────────────────────────
    def _clear_meal_badges(self):
        """기존 뱃지/오버레이 패널 제거"""
        if hasattr(self, '_badge_frame') and self._badge_frame:
            try:
                self._badge_frame.destroy()
            except Exception:
                pass
            self._badge_frame = None
        if hasattr(self, '_badge_anim_id') and self._badge_anim_id:
            try:
                self.after_cancel(self._badge_anim_id)
            except Exception:
                pass
            self._badge_anim_id = None
        self._badge_visible = False

    def _show_meal_badges(self, data, has_breakfast, has_dinner):
        """조회 버튼 우측 상단에 깜빡이는 뱃지 버튼 생성"""
        self._badge_frame = tk.Frame(self._btn_row, bg=self._bg_color())
        self._badge_frame.pack(side="right", padx=(4, 0))

        self._badge_btns  = []
        self._badge_labels = []

        badge_info = []
        if has_breakfast:
            badge_info.append((1, "☀️ 아침", "#FF8C00", data[1]))
        if has_dinner:
            badge_info.append((3, "🌙 저녁", "#5C6BC0", data[3]))

        for mc, label, badge_color, meal_data in badge_info:
            btn = tk.Button(
                self._badge_frame,
                text=label,
                font=("맑은 고딕", 10, "bold"),
                bg=badge_color, fg="white",
                relief="flat", cursor="hand2", bd=0,
                padx=8, pady=4,
                command=lambda md=meal_data, mc=mc: self._show_extra_meal(mc, md)
            )
            btn.pack(side="left", padx=2)
            self._badge_btns.append((btn, badge_color))

        self._badge_anim_state = True
        self._badge_anim_id    = None
        self._badge_visible    = True
        self._animate_badges()

    def _animate_badges(self):
        if not self._badge_visible:
            return
        try:
            for btn, base_color in self._badge_btns:
                if self._badge_anim_state:
                    btn.configure(bg=base_color)
                else:
                    btn.configure(bg="#CCCCCC")
        except Exception:
            return
        self._badge_anim_state = not self._badge_anim_state
        self._badge_anim_id = self.after(550, self._animate_badges)

    def _show_extra_meal(self, meal_code, meal_data):
        """아침/저녁 뱃지 클릭 시 팝업으로 해당 급식 표시"""
        name  = MEAL_NAMES.get(meal_code, "급식")
        icon  = "☀️" if meal_code == 1 else "🌙"
        color = "#FF8C00" if meal_code == 1 else "#5C6BC0"
        bg    = "#FFF8F0" if meal_code == 1 else "#F0F0FF"

        popup = tk.Toplevel(self)
        popup.title(f"{icon} {name} 급식")
        popup.resizable(False, False)
        popup.grab_set()
        popup.configure(bg=bg)

        # 헤더
        hdr = tk.Frame(popup, bg=color, pady=8)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"{icon}  {name} 급식",
                 font=("맑은 고딕", 14, "bold"),
                 fg="white", bg=color).pack()

        # 날짜
        wd = ["월","화","수","목","금","토","일"][self.cur_date.weekday()]
        date_str = self.cur_date.strftime(f"%Y년 %m월 %d일 ({wd})")
        tk.Label(popup, text=date_str,
                 font=("맑은 고딕", 10), bg=bg, fg="#888888").pack(pady=(8, 0))

        # 메뉴
        menu_frame = tk.Frame(popup, bg="white",
                              highlightbackground="#DDDDDD", highlightthickness=1)
        menu_frame.pack(fill="x", padx=14, pady=8, ipady=4)
        tk.Label(menu_frame, text=meal_data.get("menu", ""),
                 font=("맑은 고딕", 12),
                 bg="white", fg="#2C3A2E",
                 justify="left", wraplength=320,
                 anchor="w").pack(anchor="w", padx=14, pady=(8, 4))
        if meal_data.get("kcal"):
            kcal_clean = re.sub(r'\(해당.*?\)', '', meal_data["kcal"]).strip()
            tk.Label(menu_frame, text=f"🔥 열량: {kcal_clean}",
                     font=("맑은 고딕", 10), bg="white", fg="#8A9B8E"
                     ).pack(anchor="e", padx=14, pady=(0, 8))

        # 원산지
        if meal_data.get("orplc"):
            orplc = meal_data["orplc"].replace("<br/>","\n").replace("/","\n").strip()
            orplc_frame = tk.Frame(popup, bg="#F1F8E9",
                                   highlightbackground="#DDDDDD", highlightthickness=1)
            orplc_frame.pack(fill="x", padx=14, pady=(0, 8), ipady=4)
            tk.Label(orplc_frame, text="🌿 원산지 정보",
                     font=("맑은 고딕", 11, "bold"),
                     bg="#F1F8E9", fg="#388E3C").pack(anchor="w", padx=14, pady=(8, 4))
            tk.Label(orplc_frame, text=orplc,
                     font=("맑은 고딕", 10),
                     bg="#F1F8E9", fg="#2C3A2E",
                     justify="left", wraplength=320
                     ).pack(anchor="w", padx=14, pady=(0, 8))

        # 닫기
        tk.Button(popup, text="닫기",
                  font=("맑은 고딕", 11), bg="#BBBBBB", fg="white",
                  relief="flat", cursor="hand2", bd=0, padx=16, pady=6,
                  command=popup.destroy).pack(pady=(0, 12))

        # 팝업 중앙 배치
        popup.update_idletasks()
        px = self.winfo_rootx() + (self.winfo_width()  - popup.winfo_width())  // 2
        py = self.winfo_rooty() + (self.winfo_height() - popup.winfo_height()) // 2
        popup.geometry(f"+{px}+{py}")

    def _card(self, title, body, bg, kcal="", title_color=None):
        tc    = title_color or self._color()
        outer = tk.Frame(self.meal_frame, bg=bg,
                         highlightbackground="#DCECDA", highlightthickness=1)
        outer.pack(fill="x", pady=5, ipady=4)
        tk.Label(outer, text=title, font=("맑은 고딕", 13, "bold"),
                 bg=bg, fg=tc).pack(anchor="w", padx=14, pady=(10,4))
        tk.Label(outer, text=body, font=("맑은 고딕", 12),
                 bg=bg, fg=self.TEXT, justify="left", wraplength=450
                 ).pack(anchor="w", padx=14, pady=(0,6))
        if kcal:
            kcal_clean = re.sub(r'\(해당.*?\)', '', kcal).strip()
            tk.Label(outer, text=f"🔥 열량: {kcal_clean}",
                     font=("맑은 고딕", 10), bg=bg, fg=self.GRAY
                     ).pack(anchor="e", padx=14, pady=(0,10))


if __name__ == "__main__":
    app = MealApp()
    app.mainloop()
