# -*- coding:utf-8 -*-

txt_files_path = ".\\comsol_matlab\\txtresult"


m_files_path = ".\\comsol_matlab\\matlabcode"


matlab_code1 = """
function out = model
%
% GaIn_GaN_Si_success2.m
%
% Model exported on Jul 27 2025, 22:26 by COMSOL 6.1.0.252.

import com.comsol.model.*
import com.comsol.model.util.*

model = ModelUtil.create('Model')

model.modelPath('C:\\Users\\kkkw\\Desktop');

model.label('GaIn_GaN_Si_success2.mph');

model.param.set('air_x', '2*mar_x+sub_x');
model.param.set('air_y', '2*mar_y+sub_y');
model.param.set('air_z', '2*mar_z+sub_z+2*water_r');
model.param.set('water_r', '2');
model.param.set('d', '0.5');
model.param.set('sub_x', '10');
model.param.set('sub_y', '10');
model.param.set('sub_z', '1');
model.param.set('mar_x', '1');
model.param.set('mar_y', '1');
model.param.set('mar_z', '1');

model.component.create('comp1', true);

model.component('comp1').geom.create('geom1', 3);

model.result.table.create('evl3', 'Table');

model.component('comp1').mesh.create('mesh1');

model.component('comp1').geom('geom1').lengthUnit('mm');
model.component('comp1').geom('geom1').create('sph1', 'Sphere');
model.component('comp1').geom('geom1').feature('sph1').label('liquid');
model.component('comp1').geom('geom1').feature('sph1').set('pos', {'0' '0' 'd+water_r'});
model.component('comp1').geom('geom1').feature('sph1').set('r', 'water_r');
model.component('comp1').geom('geom1').create('blk1', 'Block');
model.component('comp1').geom('geom1').feature('blk1').label('Nitrogen');
model.component('comp1').geom('geom1').feature('blk1').set('pos', {'-(air_x)/2' '-(air_y)/2' '0'});
model.component('comp1').geom('geom1').feature('blk1').set('size', {'air_x' 'air_y' 'air_z'});
model.component('comp1').geom('geom1').create('blk2', 'Block');
model.component('comp1').geom('geom1').feature('blk2').label('left_SUB');
model.component('comp1').geom('geom1').feature('blk2').set('pos', {'-(air_x)/2' '-(air_y)/2' '-1'});
model.component('comp1').geom('geom1').feature('blk2').set('size', {'air_x/2' 'air_y' '1'});
model.component('comp1').geom('geom1').create('blk3', 'Block');
model.component('comp1').geom('geom1').feature('blk3').label('right_SUB');
model.component('comp1').geom('geom1').feature('blk3').set('pos', {'0' '-(air_y)/2' '-1'});
model.component('comp1').geom('geom1').feature('blk3').set('size', {'air_x/2' 'air_y' '1'});
model.component('comp1').geom('geom1').run;
model.component('comp1').geom('geom1').run('fin');

model.component('comp1').material.create('mat1', 'Common');
model.component('comp1').material.create('mat2', 'Common');
model.component('comp1').material.create('mat3', 'Common');
model.component('comp1').material.create('mat4', 'Common');
model.component('comp1').material('mat1').selection.set([2]);
model.component('comp1').material('mat1').propertyGroup('def').func.create('k_gas_3', 'Piecewise');
model.component('comp1').material('mat1').propertyGroup('def').func.create('C_gas_3', 'Piecewise');
model.component('comp1').material('mat1').propertyGroup('def').func.create('HC_gas_3', 'Piecewise');
model.component('comp1').material('mat1').propertyGroup('def').func.create('rho_gas_2', 'Piecewise');
model.component('comp1').material('mat1').propertyGroup('def').func.create('TD_gas_2', 'Piecewise');
model.component('comp1').material('mat1').propertyGroup('def').func.create('eta_gas_2', 'Piecewise');
model.component('comp1').material('mat2').selection.set([3]);
model.component('comp1').material('mat3').selection.set([1]);
model.component('comp1').material('mat4').selection.set([4]);

model.component('comp1').physics.create('spf2', 'LaminarFlow', 'geom1');
model.component('comp1').physics('spf2').identifier('spf2');
model.component('comp1').physics('spf2').field('velocity').field('u2');
model.component('comp1').physics('spf2').field('velocity').component({'u2' 'v2' 'w2'});
model.component('comp1').physics('spf2').field('pressure').field('p2');
model.component('comp1').physics('spf2').field('turbulentkineticenergy').field('k2');
model.component('comp1').physics('spf2').field('turbulentdissipationrate').field('ep2');
model.component('comp1').physics('spf2').field('specificdissipationrate').field('om2');
model.component('comp1').physics('spf2').field('reciprocallength').field('G2');
model.component('comp1').physics('spf2').field('correctedvelocity').field('uc2');
model.component('comp1').physics('spf2').field('correctedvelocity').component({'uc2x' 'uc2y' 'uc2z'});
model.component('comp1').physics('spf2').field('correctedpressure').field('pc2');
model.component('comp1').physics('spf2').field('turbulentkinematicviscosity').field('nutilde2');
model.component('comp1').physics('spf2').field('dimensionless1').field('yPlus2');
model.component('comp1').physics('spf2').field('dimensionless2').field('uPlus2');
model.component('comp1').physics('spf2').field('dimensionless3').field('zeta2');
model.component('comp1').physics('spf2').field('dimensionless4').field('alpha2');
model.component('comp1').physics('spf2').field('dimensionless5').field('gamma2');
model.component('comp1').physics('spf2').selection.set([2 3]);
model.component('comp1').physics('spf2').create('prpc1', 'PressurePointConstraint', 0);
model.component('comp1').physics('spf2').feature('prpc1').selection.set([2 5 18 21]);
model.component('comp1').physics.create('ls', 'LevelSet', 'geom1');
model.component('comp1').physics('ls').field('reciprocallength_i').field('GI2');
model.component('comp1').physics('ls').selection.set([2 3]);
model.component('comp1').physics('ls').create('init2', 'init', 3);
model.component('comp1').physics('ls').feature('init2').selection.set([3]);
model.component('comp1').physics.create('ht', 'HeatTransfer', 'geom1');
model.component('comp1').physics('ht').selection.set([1 4]);
model.component('comp1').physics('ht').create('init2', 'init', 3);
model.component('comp1').physics('ht').feature('init2').selection.set([4]);

model.component('comp1').multiphysics.create('tpf2', 'TwoPhaseFlowLevelSet', 3);
model.component('comp1').multiphysics('tpf2').selection.all;
model.component('comp1').multiphysics.create('ww1', 'WettedWall', 2);
model.component('comp1').multiphysics('ww1').selection.set([6 17]);
model.component('comp1').multiphysics.create('ww2', 'WettedWall', 2);
model.component('comp1').multiphysics('ww2').selection.set([17]);

model.component('comp1').mesh('mesh1').create('ftet2', 'FreeTet');

model.result.table('evl3').label('Evaluation 3D');
model.result.table('evl3').comments([native2unicode(hex2dec({'4e' 'a4'}), 'unicode')  native2unicode(hex2dec({'4e' '92'}), 'unicode')  native2unicode(hex2dec({'76' '84'}), 'unicode')  native2unicode(hex2dec({'4e' '09'}), 'unicode')  native2unicode(hex2dec({'7e' 'f4'}), 'unicode')  native2unicode(hex2dec({'50' '3c'}), 'unicode') ]);

model.component('comp1').view('view1').set('transparency', true);

model.component('comp1').material('mat1').label('Nitrogen [gas]');
model.component('comp1').material('mat1').set('family', 'custom');
model.component('comp1').material('mat1').set('customdiffuse', [0.9019607843137255 0.9019607843137255 1]);
model.component('comp1').material('mat1').set('customambient', [0.9019607843137255 0.9019607843137255 1]);
model.component('comp1').material('mat1').set('noise', true);
model.component('comp1').material('mat1').set('noisescale', 0.08);
model.component('comp1').material('mat1').set('noisefreq', 3);
model.component('comp1').material('mat1').set('lighting', 'simple');
model.component('comp1').material('mat1').propertyGroup('def').func('k_gas_3').label('Piecewise');
model.component('comp1').material('mat1').propertyGroup('def').func('k_gas_3').set('arg', 'T');
model.component('comp1').material('mat1').propertyGroup('def').func('k_gas_3').set('pieces', {'78.0' '200.0' '0.004434533-3.850398E-5*T^1+1.191155E-6*T^2-4.366716E-9*T^3+5.398442E-12*T^4'; '200.0' '673.0' '-0.003360435+1.370046E-4*T^1-1.906663E-7*T^2+2.298923E-10*T^3-1.057846E-13*T^4'; '673.0' '3273.16' '0.004026912+7.680372E-5*T^1-1.21179E-8*T^2+2.190456E-12*T^3-1.691362E-16*T^4'});
model.component('comp1').material('mat1').propertyGroup('def').func('k_gas_3').set('argunit', 'K');
model.component('comp1').material('mat1').propertyGroup('def').func('k_gas_3').set('fununit', 'W/(m*K)');
model.component('comp1').material('mat1').propertyGroup('def').func('C_gas_3').label('Piecewise 1');
model.component('comp1').material('mat1').propertyGroup('def').func('C_gas_3').set('arg', 'T');
model.component('comp1').material('mat1').propertyGroup('def').func('C_gas_3').set('pieces', {'100.0' '350.0' '1036.95879+0.0370769762*T^1-2.17115375E-4*T^2+4.13912325E-7*T^3';  ...
'350.0' '2000.0' '1148.67327-0.769706631*T^1+0.00175340478*T^2-1.40445625E-6*T^3+5.09561829E-10*T^4-7.04906094E-14*T^5';  ...
'2000.0' '9400.0' '1113.92013+0.129622119*T^1-2.60853865E-5*T^2+2.03038934E-9*T^3-1.58449E-14*T^4';  ...
'9400.0' '20000.0' '9668.78468-2.73382434*T^1+3.16263288E-4*T^2-1.46614808E-8*T^3+2.37194265E-13*T^4'});
model.component('comp1').material('mat1').propertyGroup('def').func('C_gas_3').set('argunit', 'K');
model.component('comp1').material('mat1').propertyGroup('def').func('C_gas_3').set('fununit', 'J/(kg*K)');
model.component('comp1').material('mat1').propertyGroup('def').func('HC_gas_3').label('Piecewise 2');
model.component('comp1').material('mat1').propertyGroup('def').func('HC_gas_3').set('arg', 'T');
model.component('comp1').material('mat1').propertyGroup('def').func('HC_gas_3').set('pieces', {'100.0' '350.0' '29.048738+0.00103865206*T^1-6.08213854E-6*T^2+1.15950899E-8*T^3';  ...
'350.0' '2000.0' '32.1782444-0.0215620976*T^1+4.91188211E-5*T^2-3.93435955E-8*T^3+1.42745528E-11*T^4-1.9746819E-15*T^5';  ...
'2000.0' '9400.0' '30.7020748+0.00421523356*T^1-9.82152997E-7*T^2+1.07345373E-10*T^3-5.20703821E-15*T^4+1.70489841E-19*T^5';  ...
'9400.0' '20000.0' '270.867223-0.0765837268*T^1+8.85961163E-6*T^2-4.10717967E-10*T^3+6.64461877E-15*T^4'});
model.component('comp1').material('mat1').propertyGroup('def').func('HC_gas_3').set('argunit', 'K');
model.component('comp1').material('mat1').propertyGroup('def').func('HC_gas_3').set('fununit', 'J/(mol*K)');
model.component('comp1').material('mat1').propertyGroup('def').func('rho_gas_2').label('Piecewise 3');
model.component('comp1').material('mat1').propertyGroup('def').func('rho_gas_2').set('arg', 'T');
model.component('comp1').material('mat1').propertyGroup('def').func('rho_gas_2').set('pieces', {'77.0' '3000.0' '341.3592*T^-1'});
model.component('comp1').material('mat1').propertyGroup('def').func('rho_gas_2').set('argunit', 'K');
model.component('comp1').material('mat1').propertyGroup('def').func('rho_gas_2').set('fununit', 'kg/m^3');
model.component('comp1').material('mat1').propertyGroup('def').func('TD_gas_2').label('Piecewise 4');
model.component('comp1').material('mat1').propertyGroup('def').func('TD_gas_2').set('arg', 'T');
model.component('comp1').material('mat1').propertyGroup('def').func('TD_gas_2').set('pieces', {'100.0' '165.0' '1.81553049E-9+1.24267208E-8*T^1-1.06794271E-10*T^2+3.33871206E-12*T^3-1.22105382E-14*T^4+1.50085651E-17*T^5+1.00775745E-22*T^6'; '165.0' '410.0' '-2.96215021E-6+3.7414398E-8*T^1+9.73127218E-11*T^2+3.23254922E-13*T^3-5.69914402E-16*T^4+3.23075367E-19*T^5'; '410.0' '3000.0' '-1.45215782E-5+8.13581552E-8*T^1+1.24760399E-10*T^2-1.90710466E-14*T^3+5.99943283E-18*T^4-7.71558495E-22*T^5'});
model.component('comp1').material('mat1').propertyGroup('def').func('TD_gas_2').set('argunit', 'K');
model.component('comp1').material('mat1').propertyGroup('def').func('TD_gas_2').set('fununit', 'm^2/s');
model.component('comp1').material('mat1').propertyGroup('def').func('eta_gas_2').label('Piecewise 5');
model.component('comp1').material('mat1').propertyGroup('def').func('eta_gas_2').set('arg', 'T');
model.component('comp1').material('mat1').propertyGroup('def').func('eta_gas_2').set('pieces', {'80.0' '280.0' '-1.85073E-6+1.097572E-7*T^1-3.70863E-10*T^2+1.685136E-12*T^3-4.75399E-15*T^4+5.463419E-18*T^5'; '280.0' '2150.0' '2.219433E-6+6.073737E-8*T^1-3.194531E-11*T^2+1.229863E-14*T^3-1.799528E-18*T^4'});
model.component('comp1').material('mat1').propertyGroup('def').func('eta_gas_2').set('argunit', 'K');
model.component('comp1').material('mat1').propertyGroup('def').func('eta_gas_2').set('fununit', 'Pa*s');
model.component('comp1').material('mat1').propertyGroup('def').set('thermalconductivity', {'k_gas_3(T)' '0' '0' '0' 'k_gas_3(T)' '0' '0' '0' 'k_gas_3(T)'});
model.component('comp1').material('mat1').propertyGroup('def').set('INFO_PREFIX:thermalconductivity', [native2unicode(hex2dec({'5f' '15'}), 'unicode')  native2unicode(hex2dec({'75' '28'}), 'unicode') ': below -173C (100K): C.Y. Ho, R.W. Powell and P.E. Liley, Journal of Physical and Chemical Reference Data, v1, No. 2, p279 (1972) available online at https://srd.nist.gov/JPCRD/jpcrd7.pdf, above -173C (100K): F.J. Uribe, E.A. Mason and J. Kestin, Journal of Physical and Chemical Reference Data, v19, No. 5, p1123 (1990) available online at https://srd.nist.gov/JPCRD/jpcrd396.pdf\\n' native2unicode(hex2dec({'6c' 'e8'}), 'unicode') ': Tmp near -209.9C (63.2K), data for N2, data from Ho et. al. was multiplied by 0.916 to match the higher temperature data']);
model.component('comp1').material('mat1').propertyGroup('def').set('heatcapacity', 'C_gas_3(T)');
model.component('comp1').material('mat1').propertyGroup('def').set('INFO_PREFIX:heatcapacity', [native2unicode(hex2dec({'5f' '15'}), 'unicode')  native2unicode(hex2dec({'75' '28'}), 'unicode') ': B.J. McBride, S. Gordon and M.A. Reno, Thermodynamic Data for Fifty Reference Elements, NASA Technical Paper 3287 (1993) available online at https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20010021116.pdf\\n' native2unicode(hex2dec({'6c' 'e8'}), 'unicode') ': Tmp near -209.9C (63.2K)']);
model.component('comp1').material('mat1').propertyGroup('def').set('HC', 'HC_gas_3(T)');
model.component('comp1').material('mat1').propertyGroup('def').set('INFO_PREFIX:HC', [native2unicode(hex2dec({'5f' '15'}), 'unicode')  native2unicode(hex2dec({'75' '28'}), 'unicode') ': B.J. McBride, S. Gordon and M.A. Reno, Thermodynamic Data for Fifty Reference Elements, NASA Technical Paper 3287 (1993) available online at https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20010021116.pdf\\n' native2unicode(hex2dec({'6c' 'e8'}), 'unicode') ': Tmp near -209.9C (63.2K), data for N2']);
model.component('comp1').material('mat1').propertyGroup('def').set('density', 'rho_gas_2(T)');
model.component('comp1').material('mat1').propertyGroup('def').set('INFO_PREFIX:density', [native2unicode(hex2dec({'5f' '15'}), 'unicode')  native2unicode(hex2dec({'75' '28'}), 'unicode') ': value at 0C (273K) from Wikipedia with the temperature dependence from the ideal gas law\\n' native2unicode(hex2dec({'6c' 'e8'}), 'unicode') ': Tmp near -209.9C (63.2K), data is for N2, dry gas at 1 atm pressure']);
model.component('comp1').material('mat1').propertyGroup('def').set('TD', 'TD_gas_2(T)');
model.component('comp1').material('mat1').propertyGroup('def').set('INFO_PREFIX:TD', [native2unicode(hex2dec({'5f' '15'}), 'unicode')  native2unicode(hex2dec({'75' '28'}), 'unicode') ': calculated from the thermal conductivity, density, and specific heat\\n' native2unicode(hex2dec({'6c' 'e8'}), 'unicode') ': Tmp near -209.9C (63.2K)']);
model.component('comp1').material('mat1').propertyGroup('def').set('dynamicviscosity', 'eta_gas_2(T)');
model.component('comp1').material('mat1').propertyGroup('def').set('INFO_PREFIX:dynamicviscosity', [native2unicode(hex2dec({'5f' '15'}), 'unicode')  native2unicode(hex2dec({'75' '28'}), 'unicode') ': K. Stephan, R. Krauss and A. Laesecke, Journal of Physical and Chemical Reference Data, v16, No. 4, p993 (1987) available online at https://srd.nist.gov/jpcrdreprint/1.555798.pdf and W.A. Cole and W.A. Wakeman, Journal of Physical and Chemical Reference Data, v14, No. 1, p209 (1985) available online at https://srd.nist.gov/JPCRD/jpcrd268.pdf\\n' native2unicode(hex2dec({'6c' 'e8'}), 'unicode') ': Tmp near -209.9C (63.2K), data for 1 bar pressure, other pressures given in reference']);
model.component('comp1').material('mat1').propertyGroup('def').addInput('temperature');
"""

matlab_code2 = """
model.component('comp1').mesh('mesh1').feature('size').set('table', 'cfd');
model.component('comp1').mesh('mesh1').run;

model.study.create('std1');
model.study('std1').create('phasei', 'PhaseInitialization');
model.study('std1').create('time', 'Transient');
model.study('std1').feature('phasei').set('activate', {'spf2' 'off' 'ls' 'on' 'ht' 'on' 'frame:spatial1' 'on' 'frame:material1' 'on'});

model.sol.create('sol1');
model.sol('sol1').study('std1');
model.sol('sol1').attach('std1');
model.sol('sol1').create('st1', 'StudyStep');
model.sol('sol1').create('v1', 'Variables');
model.sol('sol1').create('s1', 'Stationary');
model.sol('sol1').create('su1', 'StoreSolution');
model.sol('sol1').create('st2', 'StudyStep');
model.sol('sol1').create('v2', 'Variables');
model.sol('sol1').create('t1', 'Time');
model.sol('sol1').feature('s1').create('fc1', 'FullyCoupled');
model.sol('sol1').feature('s1').create('d1', 'Direct');
model.sol('sol1').feature('s1').create('i1', 'Iterative');
model.sol('sol1').feature('s1').feature('i1').create('mg1', 'Multigrid');
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('pr').create('sl1', 'SORLine');
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('po').create('sl1', 'SORLine');
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('cs').create('d1', 'Direct');
model.sol('sol1').feature('s1').feature.remove('fcDef');
model.sol('sol1').feature('t1').create('se1', 'Segregated');
model.sol('sol1').feature('t1').create('d1', 'Direct');
model.sol('sol1').feature('t1').create('d2', 'Direct');
model.sol('sol1').feature('t1').create('d3', 'Direct');
model.sol('sol1').feature('t1').create('i1', 'Iterative');
model.sol('sol1').feature('t1').create('i2', 'Iterative');
model.sol('sol1').feature('t1').create('i3', 'Iterative');
model.sol('sol1').feature('t1').feature('se1').create('ss1', 'SegregatedStep');
model.sol('sol1').feature('t1').feature('se1').create('ss2', 'SegregatedStep');
model.sol('sol1').feature('t1').feature('se1').create('ss3', 'SegregatedStep');
model.sol('sol1').feature('t1').feature('se1').create('ll1', 'LowerLimit');
model.sol('sol1').feature('t1').feature('se1').feature.remove('ssDef');
model.sol('sol1').feature('t1').feature('i1').create('mg1', 'Multigrid');
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('pr').create('so1', 'SOR');
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('po').create('so1', 'SOR');
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('cs').create('d1', 'Direct');
model.sol('sol1').feature('t1').feature('i2').create('mg1', 'Multigrid');
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('pr').create('sc1', 'SCGS');
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('po').create('sc1', 'SCGS');
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('cs').create('d1', 'Direct');
model.sol('sol1').feature('t1').feature('i3').create('mg1', 'Multigrid');
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('pr').create('sl1', 'SORLine');
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('po').create('sl1', 'SORLine');
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('cs').create('d1', 'Direct');
model.sol('sol1').feature('t1').feature.remove('fcDef');

model.result.dataset.create('surf1', 'Surface');
model.result.dataset('surf1').selection.set([4 5 7 9 24]);
model.result.create('pg1', 'PlotGroup3D');
model.result.create('pg2', 'PlotGroup3D');
model.result.create('pg3', 'PlotGroup3D');
model.result('pg1').create('slc1', 'Slice');
model.result('pg2').create('surf1', 'Surface');
model.result('pg2').feature('surf1').set('expr', 'p2');
model.result('pg2').feature('surf1').create('tran1', 'Transparency');
model.result('pg3').create('slc1', 'Slice');
model.result('pg3').create('iso1', 'Isosurface');
model.result('pg3').feature('slc1').set('expr', 'ls.Vf1');
model.result('pg3').feature('iso1').set('data', 'dset1');
model.result('pg3').feature('iso1').set('expr', 'ls.Vf1');
model.result.export.create('plot1', 'Plot');

model.study('std1').feature('phasei').set('plot', true);
model.study('std1').feature('phasei').set('plotgroup', 'pg3');
model.study('std1').feature('time').set('tlist', 'range(0,0.002,0.2)');
model.study('std1').feature('time').set('plot', true);
model.study('std1').feature('time').set('plotgroup', 'pg3');
model.study('std1').feature('time').set('useinitsol', true);
model.study('std1').feature('time').set('initstudy', 'std1');
model.study('std1').feature('time').set('solnum', 'auto');

model.sol('sol1').attach('std1');
model.sol('sol1').feature('st1').label([native2unicode(hex2dec({'7f' '16'}), 'unicode')  native2unicode(hex2dec({'8b' 'd1'}), 'unicode')  native2unicode(hex2dec({'65' 'b9'}), 'unicode')  native2unicode(hex2dec({'7a' '0b'}), 'unicode') ': ' native2unicode(hex2dec({'76' 'f8'}), 'unicode')  native2unicode(hex2dec({'52' '1d'}), 'unicode')  native2unicode(hex2dec({'59' 'cb'}), 'unicode')  native2unicode(hex2dec({'53' '16'}), 'unicode') ]);
model.sol('sol1').feature('v1').label([native2unicode(hex2dec({'56' 'e0'}), 'unicode')  native2unicode(hex2dec({'53' 'd8'}), 'unicode')  native2unicode(hex2dec({'91' 'cf'}), 'unicode') ' 1.1']);
model.sol('sol1').feature('v1').set('clist', {'2.0E-4[s]'});
model.sol('sol1').feature('s1').label([native2unicode(hex2dec({'7a' '33'}), 'unicode')  native2unicode(hex2dec({'60' '01'}), 'unicode')  native2unicode(hex2dec({'6c' '42'}), 'unicode')  native2unicode(hex2dec({'89' 'e3'}), 'unicode')  native2unicode(hex2dec({'56' '68'}), 'unicode') ' 1.1']);
model.sol('sol1').feature('s1').feature('dDef').label([native2unicode(hex2dec({'76' 'f4'}), 'unicode')  native2unicode(hex2dec({'63' 'a5'}), 'unicode') ' 2']);
model.sol('sol1').feature('s1').feature('aDef').label([native2unicode(hex2dec({'9a' 'd8'}), 'unicode')  native2unicode(hex2dec({'7e' 'a7'}), 'unicode') ' 1']);
model.sol('sol1').feature('s1').feature('aDef').set('cachepattern', true);
model.sol('sol1').feature('s1').feature('fc1').label([native2unicode(hex2dec({'51' '68'}), 'unicode')  native2unicode(hex2dec({'80' '26'}), 'unicode')  native2unicode(hex2dec({'54' '08'}), 'unicode') ' 1.1']);
model.sol('sol1').feature('s1').feature('fc1').set('linsolver', 'd1');
model.sol('sol1').feature('s1').feature('fc1').set('initstep', 0.01);
model.sol('sol1').feature('s1').feature('fc1').set('minstep', 1.0E-6);
model.sol('sol1').feature('s1').feature('fc1').set('maxiter', 50);
model.sol('sol1').feature('s1').feature('d1').label([native2unicode(hex2dec({'76' 'f4'}), 'unicode')  native2unicode(hex2dec({'63' 'a5'}), 'unicode')  native2unicode(hex2dec({'ff' '0c'}), 'unicode')  native2unicode(hex2dec({'75' '4c'}), 'unicode')  native2unicode(hex2dec({'97' '62'}), 'unicode')  native2unicode(hex2dec({'8d' 'dd'}), 'unicode')  native2unicode(hex2dec({'79' 'bb'}), 'unicode') ' (ls)']);
model.sol('sol1').feature('s1').feature('d1').set('linsolver', 'pardiso');
model.sol('sol1').feature('s1').feature('d1').set('pivotperturb', 1.0E-13);
model.sol('sol1').feature('s1').feature('i1').label(['AMG' native2unicode(hex2dec({'ff' '0c'}), 'unicode')  native2unicode(hex2dec({'75' '4c'}), 'unicode')  native2unicode(hex2dec({'97' '62'}), 'unicode')  native2unicode(hex2dec({'8d' 'dd'}), 'unicode')  native2unicode(hex2dec({'79' 'bb'}), 'unicode') ' (ls)']);
model.sol('sol1').feature('s1').feature('i1').set('nlinnormuse', true);
model.sol('sol1').feature('s1').feature('i1').set('maxlinit', 1000);
model.sol('sol1').feature('s1').feature('i1').feature('ilDef').label([native2unicode(hex2dec({'4e' '0d'}), 'unicode')  native2unicode(hex2dec({'5b' '8c'}), 'unicode')  native2unicode(hex2dec({'51' '68'}), 'unicode') ' LU ' native2unicode(hex2dec({'52' '06'}), 'unicode')  native2unicode(hex2dec({'89' 'e3'}), 'unicode') ' 1']);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').label([native2unicode(hex2dec({'59' '1a'}), 'unicode')  native2unicode(hex2dec({'91' 'cd'}), 'unicode')  native2unicode(hex2dec({'7f' '51'}), 'unicode')  native2unicode(hex2dec({'68' '3c'}), 'unicode') ' 1.1']);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').set('prefun', 'saamg');
model.sol('sol1').feature('s1').feature('i1').feature('mg1').set('maxcoarsedof', 50000);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').set('saamgcompwise', true);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').set('usesmooth', false);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('pr').label([native2unicode(hex2dec({'98' '84'}), 'unicode')  native2unicode(hex2dec({'5e' '73'}), 'unicode')  native2unicode(hex2dec({'6e' 'd1'}), 'unicode')  native2unicode(hex2dec({'56' '68'}), 'unicode') ' 1']);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('pr').feature('soDef').label('SOR 1');
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('pr').feature('sl1').label('SOR Line 1.1');
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('pr').feature('sl1').set('linesweeptype', 'ssor');
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('pr').feature('sl1').set('iter', 1);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('pr').feature('sl1').set('linerelax', 0.7);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('pr').feature('sl1').set('linemethod', 'uncoupled');
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('pr').feature('sl1').set('relax', 0.5);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('po').label([native2unicode(hex2dec({'54' '0e'}), 'unicode')  native2unicode(hex2dec({'5e' '73'}), 'unicode')  native2unicode(hex2dec({'6e' 'd1'}), 'unicode')  native2unicode(hex2dec({'56' '68'}), 'unicode') ' 1']);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('po').feature('soDef').label('SOR 1');
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('po').feature('sl1').label('SOR Line 1.1');
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('po').feature('sl1').set('linesweeptype', 'ssor');
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('po').feature('sl1').set('iter', 1);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('po').feature('sl1').set('linerelax', 0.7);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('po').feature('sl1').set('linemethod', 'uncoupled');
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('po').feature('sl1').set('relax', 0.5);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('cs').label([native2unicode(hex2dec({'7c' '97'}), 'unicode')  native2unicode(hex2dec({'53' '16'}), 'unicode')  native2unicode(hex2dec({'6c' '42'}), 'unicode')  native2unicode(hex2dec({'89' 'e3'}), 'unicode')  native2unicode(hex2dec({'56' '68'}), 'unicode') ' 1']);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('cs').feature('dDef').label([native2unicode(hex2dec({'76' 'f4'}), 'unicode')  native2unicode(hex2dec({'63' 'a5'}), 'unicode') ' 2']);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('cs').feature('d1').label([native2unicode(hex2dec({'76' 'f4'}), 'unicode')  native2unicode(hex2dec({'63' 'a5'}), 'unicode') ' 1.1']);
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('cs').feature('d1').set('linsolver', 'pardiso');
model.sol('sol1').feature('s1').feature('i1').feature('mg1').feature('cs').feature('d1').set('pivotperturb', 1.0E-13);
model.sol('sol1').feature('su1').label([native2unicode(hex2dec({'89' 'e3'}), 'unicode')  native2unicode(hex2dec({'5b' '58'}), 'unicode')  native2unicode(hex2dec({'50' 'a8'}), 'unicode') ' 1.1']);
model.sol('sol1').feature('st2').label([native2unicode(hex2dec({'7f' '16'}), 'unicode')  native2unicode(hex2dec({'8b' 'd1'}), 'unicode')  native2unicode(hex2dec({'65' 'b9'}), 'unicode')  native2unicode(hex2dec({'7a' '0b'}), 'unicode') ': ' native2unicode(hex2dec({'77' 'ac'}), 'unicode')  native2unicode(hex2dec({'60' '01'}), 'unicode') ]);
model.sol('sol1').feature('st2').set('studystep', 'time');
model.sol('sol1').feature('v2').label([native2unicode(hex2dec({'56' 'e0'}), 'unicode')  native2unicode(hex2dec({'53' 'd8'}), 'unicode')  native2unicode(hex2dec({'91' 'cf'}), 'unicode') ' 2.1']);
model.sol('sol1').feature('v2').set('initsol', 'sol1');
model.sol('sol1').feature('v2').set('solnum', 'auto');
model.sol('sol1').feature('v2').set('resscalemethod', 'manual');
model.sol('sol1').feature('v2').set('notsolmethod', 'sol');
model.sol('sol1').feature('v2').set('notsol', 'sol1');
model.sol('sol1').feature('v2').set('notsoluse', 'sol2');
model.sol('sol1').feature('v2').set('notsolnum', 'auto');
model.sol('sol1').feature('v2').set('clist', {'range(0,0.002,0.2)' '2.0E-4[s]'});
model.sol('sol1').feature('v2').feature('comp1_phils').set('scalemethod', 'manual');
model.sol('sol1').feature('v2').feature('comp1_phils').set('scaleval', 1);
model.sol('sol1').feature('t1').label([native2unicode(hex2dec({'77' 'ac'}), 'unicode')  native2unicode(hex2dec({'60' '01'}), 'unicode')  native2unicode(hex2dec({'6c' '42'}), 'unicode')  native2unicode(hex2dec({'89' 'e3'}), 'unicode')  native2unicode(hex2dec({'56' '68'}), 'unicode') ' 1.1']);
model.sol('sol1').feature('t1').set('control', 'time');
model.sol('sol1').feature('t1').set('tlist', 'range(0,0.002,0.2)');
model.sol('sol1').feature('t1').set('rtol', 0.005);
model.sol('sol1').feature('t1').set('atolglobalfactor', 0.05);
model.sol('sol1').feature('t1').set('atolmethod', {'comp1_GI2' 'global' 'comp1_p2' 'scaled' 'comp1_phils' 'scaled' 'comp1_T' 'global' 'comp1_u2' 'global'});
model.sol('sol1').feature('t1').set('atolfactor', {'comp1_GI2' '0.1' 'comp1_p2' '1' 'comp1_phils' '0.01' 'comp1_T' '0.1' 'comp1_u2' '0.1'});
model.sol('sol1').feature('t1').set('maxorder', 2);
model.sol('sol1').feature('t1').set('stabcntrl', true);
model.sol('sol1').feature('t1').set('bwinitstepfrac', 0.01);
model.sol('sol1').feature('t1').set('estrat', 'exclude');
model.sol('sol1').feature('t1').set('rescaleafterinitbw', true);
model.sol('sol1').feature('t1').set('plot', true);
model.sol('sol1').feature('t1').set('plotgroup', 'pg3');
model.sol('sol1').feature('t1').feature('dDef').label([native2unicode(hex2dec({'76' 'f4'}), 'unicode')  native2unicode(hex2dec({'63' 'a5'}), 'unicode') ' 4']);
model.sol('sol1').feature('t1').feature('aDef').label([native2unicode(hex2dec({'9a' 'd8'}), 'unicode')  native2unicode(hex2dec({'7e' 'a7'}), 'unicode') ' 1']);
model.sol('sol1').feature('t1').feature('aDef').set('cachepattern', true);
model.sol('sol1').feature('t1').feature('se1').label([native2unicode(hex2dec({'52' '06'}), 'unicode')  native2unicode(hex2dec({'79' 'bb'}), 'unicode') ' 1.1']);
model.sol('sol1').feature('t1').feature('se1').set('ntolfact', 0.5);
model.sol('sol1').feature('t1').feature('se1').set('segstabacc', 'segaacc');
model.sol('sol1').feature('t1').feature('se1').set('segaaccdim', 5);
model.sol('sol1').feature('t1').feature('se1').set('segaaccmix', 0.9);
model.sol('sol1').feature('t1').feature('se1').set('segaaccdelay', 1);
model.sol('sol1').feature('t1').feature('se1').feature('ss1').label([native2unicode(hex2dec({'6e' '29'}), 'unicode')  native2unicode(hex2dec({'5e' 'a6'}), 'unicode') ]);
model.sol('sol1').feature('t1').feature('se1').feature('ss1').set('segvar', {'comp1_T'});
model.sol('sol1').feature('t1').feature('se1').feature('ss1').set('linsolver', 'd1');
model.sol('sol1').feature('t1').feature('se1').feature('ss1').set('subdamp', '0.8');
model.sol('sol1').feature('t1').feature('se1').feature('ss1').set('subjtech', 'once');
model.sol('sol1').feature('t1').feature('se1').feature('ss2').label([native2unicode(hex2dec({'90' '1f'}), 'unicode')  native2unicode(hex2dec({'5e' 'a6'}), 'unicode') ' u2' native2unicode(hex2dec({'ff' '0c'}), 'unicode')  native2unicode(hex2dec({'53' '8b'}), 'unicode')  native2unicode(hex2dec({'52' '9b'}), 'unicode') ' p2']);
model.sol('sol1').feature('t1').feature('se1').feature('ss2').set('segvar', {'comp1_u2' 'comp1_p2'});
model.sol('sol1').feature('t1').feature('se1').feature('ss2').set('linsolver', 'd2');
model.sol('sol1').feature('t1').feature('se1').feature('ss2').set('subdamp', '0.8');
model.sol('sol1').feature('t1').feature('se1').feature('ss2').set('subjtech', 'once');
model.sol('sol1').feature('t1').feature('se1').feature('ss3').label([native2unicode(hex2dec({'6c' '34'}), 'unicode')  native2unicode(hex2dec({'5e' '73'}), 'unicode')  native2unicode(hex2dec({'96' 'c6'}), 'unicode')  native2unicode(hex2dec({'53' 'd8'}), 'unicode')  native2unicode(hex2dec({'91' 'cf'}), 'unicode')  native2unicode(hex2dec({'ff' '0c'}), 'unicode') 'phils']);
model.sol('sol1').feature('t1').feature('se1').feature('ss3').set('segvar', {'comp1_phils'});
model.sol('sol1').feature('t1').feature('se1').feature('ss3').set('linsolver', 'd3');
model.sol('sol1').feature('t1').feature('se1').feature('ss3').set('subdamp', '0.8');
model.sol('sol1').feature('t1').feature('se1').feature('ss3').set('subjtech', 'once');
model.sol('sol1').feature('t1').feature('se1').feature('ll1').label([native2unicode(hex2dec({'4e' '0b'}), 'unicode')  native2unicode(hex2dec({'96' '50'}), 'unicode') ' 1.1']);
model.sol('sol1').feature('t1').feature('se1').feature('ll1').set('lowerlimit', 'comp1.T 0 ');
model.sol('sol1').feature('t1').feature('se1').feature.remove('ht1');
model.sol('sol1').feature('t1').feature('d1').label([native2unicode(hex2dec({'76' 'f4'}), 'unicode')  native2unicode(hex2dec({'63' 'a5'}), 'unicode')  native2unicode(hex2dec({'ff' '0c'}), 'unicode')  native2unicode(hex2dec({'4f' '20'}), 'unicode')  native2unicode(hex2dec({'70' 'ed'}), 'unicode')  native2unicode(hex2dec({'53' 'd8'}), 'unicode')  native2unicode(hex2dec({'91' 'cf'}), 'unicode') ' (ht)']);
model.sol('sol1').feature('t1').feature('d1').set('linsolver', 'pardiso');
model.sol('sol1').feature('t1').feature('d1').set('pivotperturb', 1.0E-13);
model.sol('sol1').feature('t1').feature('d2').label([native2unicode(hex2dec({'76' 'f4'}), 'unicode')  native2unicode(hex2dec({'63' 'a5'}), 'unicode')  native2unicode(hex2dec({'ff' '0c'}), 'unicode')  native2unicode(hex2dec({'6d' '41'}), 'unicode')  native2unicode(hex2dec({'4f' '53'}), 'unicode')  native2unicode(hex2dec({'6d' '41'}), 'unicode')  native2unicode(hex2dec({'52' 'a8'}), 'unicode')  native2unicode(hex2dec({'53' 'd8'}), 'unicode')  native2unicode(hex2dec({'91' 'cf'}), 'unicode') ' (spf2)']);
model.sol('sol1').feature('t1').feature('d2').set('linsolver', 'pardiso');
model.sol('sol1').feature('t1').feature('d2').set('pivotperturb', 1.0E-13);
model.sol('sol1').feature('t1').feature('d3').label([native2unicode(hex2dec({'76' 'f4'}), 'unicode')  native2unicode(hex2dec({'63' 'a5'}), 'unicode')  native2unicode(hex2dec({'ff' '0c'}), 'unicode')  native2unicode(hex2dec({'6c' '34'}), 'unicode')  native2unicode(hex2dec({'5e' '73'}), 'unicode')  native2unicode(hex2dec({'96' 'c6'}), 'unicode')  native2unicode(hex2dec({'53' 'd8'}), 'unicode')  native2unicode(hex2dec({'91' 'cf'}), 'unicode') ' (ls)']);
model.sol('sol1').feature('t1').feature('d3').set('linsolver', 'pardiso');
model.sol('sol1').feature('t1').feature('d3').set('pivotperturb', 1.0E-13);
model.sol('sol1').feature('t1').feature('i1').label(['AMG' native2unicode(hex2dec({'ff' '0c'}), 'unicode')  native2unicode(hex2dec({'4f' '20'}), 'unicode')  native2unicode(hex2dec({'70' 'ed'}), 'unicode')  native2unicode(hex2dec({'53' 'd8'}), 'unicode')  native2unicode(hex2dec({'91' 'cf'}), 'unicode') ' (ht)']);
model.sol('sol1').feature('t1').feature('i1').set('rhob', 20);
model.sol('sol1').feature('t1').feature('i1').feature('ilDef').label([native2unicode(hex2dec({'4e' '0d'}), 'unicode')  native2unicode(hex2dec({'5b' '8c'}), 'unicode')  native2unicode(hex2dec({'51' '68'}), 'unicode') ' LU ' native2unicode(hex2dec({'52' '06'}), 'unicode')  native2unicode(hex2dec({'89' 'e3'}), 'unicode') ' 1']);
model.sol('sol1').feature('t1').feature('i1').feature('mg1').label([native2unicode(hex2dec({'59' '1a'}), 'unicode')  native2unicode(hex2dec({'91' 'cd'}), 'unicode')  native2unicode(hex2dec({'7f' '51'}), 'unicode')  native2unicode(hex2dec({'68' '3c'}), 'unicode') ' 1.1']);
model.sol('sol1').feature('t1').feature('i1').feature('mg1').set('prefun', 'saamg');
model.sol('sol1').feature('t1').feature('i1').feature('mg1').set('maxcoarsedof', 50000);
model.sol('sol1').feature('t1').feature('i1').feature('mg1').set('saamgcompwise', true);
model.sol('sol1').feature('t1').feature('i1').feature('mg1').set('usesmooth', false);
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('pr').label([native2unicode(hex2dec({'98' '84'}), 'unicode')  native2unicode(hex2dec({'5e' '73'}), 'unicode')  native2unicode(hex2dec({'6e' 'd1'}), 'unicode')  native2unicode(hex2dec({'56' '68'}), 'unicode') ' 1']);
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('pr').feature('soDef').label('SOR 2');
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('pr').feature('so1').label('SOR 1.1');
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('pr').feature('so1').set('relax', 0.9);
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('po').label([native2unicode(hex2dec({'54' '0e'}), 'unicode')  native2unicode(hex2dec({'5e' '73'}), 'unicode')  native2unicode(hex2dec({'6e' 'd1'}), 'unicode')  native2unicode(hex2dec({'56' '68'}), 'unicode') ' 1']);
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('po').feature('soDef').label('SOR 2');
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('po').feature('so1').label('SOR 1.1');
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('po').feature('so1').set('relax', 0.9);
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('cs').label([native2unicode(hex2dec({'7c' '97'}), 'unicode')  native2unicode(hex2dec({'53' '16'}), 'unicode')  native2unicode(hex2dec({'6c' '42'}), 'unicode')  native2unicode(hex2dec({'89' 'e3'}), 'unicode')  native2unicode(hex2dec({'56' '68'}), 'unicode') ' 1']);
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('cs').feature('dDef').label([native2unicode(hex2dec({'76' 'f4'}), 'unicode')  native2unicode(hex2dec({'63' 'a5'}), 'unicode') ' 2']);
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('cs').feature('d1').label([native2unicode(hex2dec({'76' 'f4'}), 'unicode')  native2unicode(hex2dec({'63' 'a5'}), 'unicode') ' 1.1']);
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('cs').feature('d1').set('linsolver', 'pardiso');
model.sol('sol1').feature('t1').feature('i1').feature('mg1').feature('cs').feature('d1').set('pivotperturb', 1.0E-13);
model.sol('sol1').feature('t1').feature('i2').label(['AMG' native2unicode(hex2dec({'ff' '0c'}), 'unicode')  native2unicode(hex2dec({'6d' '41'}), 'unicode')  native2unicode(hex2dec({'4f' '53'}), 'unicode')  native2unicode(hex2dec({'6d' '41'}), 'unicode')  native2unicode(hex2dec({'52' 'a8'}), 'unicode')  native2unicode(hex2dec({'53' 'd8'}), 'unicode')  native2unicode(hex2dec({'91' 'cf'}), 'unicode') ' (spf2)']);
model.sol('sol1').feature('t1').feature('i2').set('maxlinit', 100);
model.sol('sol1').feature('t1').feature('i2').set('rhob', 20);
model.sol('sol1').feature('t1').feature('i2').feature('ilDef').label([native2unicode(hex2dec({'4e' '0d'}), 'unicode')  native2unicode(hex2dec({'5b' '8c'}), 'unicode')  native2unicode(hex2dec({'51' '68'}), 'unicode') ' LU ' native2unicode(hex2dec({'52' '06'}), 'unicode')  native2unicode(hex2dec({'89' 'e3'}), 'unicode') ' 1']);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').label([native2unicode(hex2dec({'59' '1a'}), 'unicode')  native2unicode(hex2dec({'91' 'cd'}), 'unicode')  native2unicode(hex2dec({'7f' '51'}), 'unicode')  native2unicode(hex2dec({'68' '3c'}), 'unicode') ' 1.1']);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').set('prefun', 'saamg');
model.sol('sol1').feature('t1').feature('i2').feature('mg1').set('maxcoarsedof', 80000);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').set('strconn', 0.02);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').set('saamgcompwise', true);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').set('usesmooth', false);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('pr').label([native2unicode(hex2dec({'98' '84'}), 'unicode')  native2unicode(hex2dec({'5e' '73'}), 'unicode')  native2unicode(hex2dec({'6e' 'd1'}), 'unicode')  native2unicode(hex2dec({'56' '68'}), 'unicode') ' 1']);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('pr').feature('soDef').label('SOR 1');
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('pr').feature('sc1').label('SCGS 1.1');
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('pr').feature('sc1').set('linesweeptype', 'ssor');
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('pr').feature('sc1').set('iter', 0);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('pr').feature('sc1').set('approxscgs', true);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('pr').feature('sc1').set('scgsdirectmaxsize', 1000);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('po').label([native2unicode(hex2dec({'54' '0e'}), 'unicode')  native2unicode(hex2dec({'5e' '73'}), 'unicode')  native2unicode(hex2dec({'6e' 'd1'}), 'unicode')  native2unicode(hex2dec({'56' '68'}), 'unicode') ' 1']);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('po').feature('soDef').label('SOR 1');
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('po').feature('sc1').label('SCGS 1.1');
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('po').feature('sc1').set('linesweeptype', 'ssor');
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('po').feature('sc1').set('iter', 1);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('po').feature('sc1').set('approxscgs', true);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('po').feature('sc1').set('scgsdirectmaxsize', 1000);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('cs').label([native2unicode(hex2dec({'7c' '97'}), 'unicode')  native2unicode(hex2dec({'53' '16'}), 'unicode')  native2unicode(hex2dec({'6c' '42'}), 'unicode')  native2unicode(hex2dec({'89' 'e3'}), 'unicode')  native2unicode(hex2dec({'56' '68'}), 'unicode') ' 1']);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('cs').feature('dDef').label([native2unicode(hex2dec({'76' 'f4'}), 'unicode')  native2unicode(hex2dec({'63' 'a5'}), 'unicode') ' 2']);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('cs').feature('d1').label([native2unicode(hex2dec({'76' 'f4'}), 'unicode')  native2unicode(hex2dec({'63' 'a5'}), 'unicode') ' 1.1']);
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('cs').feature('d1').set('linsolver', 'pardiso');
model.sol('sol1').feature('t1').feature('i2').feature('mg1').feature('cs').feature('d1').set('pivotperturb', 1.0E-13);
model.sol('sol1').feature('t1').feature('i3').label(['AMG' native2unicode(hex2dec({'ff' '0c'}), 'unicode')  native2unicode(hex2dec({'6c' '34'}), 'unicode')  native2unicode(hex2dec({'5e' '73'}), 'unicode')  native2unicode(hex2dec({'96' 'c6'}), 'unicode')  native2unicode(hex2dec({'53' 'd8'}), 'unicode')  native2unicode(hex2dec({'91' 'cf'}), 'unicode') ' (ls)']);
model.sol('sol1').feature('t1').feature('i3').set('maxlinit', 50);
model.sol('sol1').feature('t1').feature('i3').set('rhob', 20);
model.sol('sol1').feature('t1').feature('i3').feature('ilDef').label([native2unicode(hex2dec({'4e' '0d'}), 'unicode')  native2unicode(hex2dec({'5b' '8c'}), 'unicode')  native2unicode(hex2dec({'51' '68'}), 'unicode') ' LU ' native2unicode(hex2dec({'52' '06'}), 'unicode')  native2unicode(hex2dec({'89' 'e3'}), 'unicode') ' 1']);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').label([native2unicode(hex2dec({'59' '1a'}), 'unicode')  native2unicode(hex2dec({'91' 'cd'}), 'unicode')  native2unicode(hex2dec({'7f' '51'}), 'unicode')  native2unicode(hex2dec({'68' '3c'}), 'unicode') ' 1.1']);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').set('prefun', 'saamg');
model.sol('sol1').feature('t1').feature('i3').feature('mg1').set('maxcoarsedof', 50000);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').set('saamgcompwise', true);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').set('usesmooth', false);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('pr').label([native2unicode(hex2dec({'98' '84'}), 'unicode')  native2unicode(hex2dec({'5e' '73'}), 'unicode')  native2unicode(hex2dec({'6e' 'd1'}), 'unicode')  native2unicode(hex2dec({'56' '68'}), 'unicode') ' 1']);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('pr').feature('soDef').label('SOR 1');
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('pr').feature('sl1').label('SOR Line 1.1');
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('pr').feature('sl1').set('linesweeptype', 'ssor');
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('pr').feature('sl1').set('iter', 1);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('pr').feature('sl1').set('linerelax', 0.7);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('pr').feature('sl1').set('relax', 0.5);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('po').label([native2unicode(hex2dec({'54' '0e'}), 'unicode')  native2unicode(hex2dec({'5e' '73'}), 'unicode')  native2unicode(hex2dec({'6e' 'd1'}), 'unicode')  native2unicode(hex2dec({'56' '68'}), 'unicode') ' 1']);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('po').feature('soDef').label('SOR 1');
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('po').feature('sl1').label('SOR Line 1.1');
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('po').feature('sl1').set('linesweeptype', 'ssor');
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('po').feature('sl1').set('iter', 1);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('po').feature('sl1').set('linerelax', 0.7);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('po').feature('sl1').set('relax', 0.5);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('cs').label([native2unicode(hex2dec({'7c' '97'}), 'unicode')  native2unicode(hex2dec({'53' '16'}), 'unicode')  native2unicode(hex2dec({'6c' '42'}), 'unicode')  native2unicode(hex2dec({'89' 'e3'}), 'unicode')  native2unicode(hex2dec({'56' '68'}), 'unicode') ' 1']);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('cs').feature('dDef').label([native2unicode(hex2dec({'76' 'f4'}), 'unicode')  native2unicode(hex2dec({'63' 'a5'}), 'unicode') ' 2']);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('cs').feature('d1').label([native2unicode(hex2dec({'76' 'f4'}), 'unicode')  native2unicode(hex2dec({'63' 'a5'}), 'unicode') ' 1.1']);
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('cs').feature('d1').set('linsolver', 'pardiso');
model.sol('sol1').feature('t1').feature('i3').feature('mg1').feature('cs').feature('d1').set('pivotperturb', 1.0E-13);
model.sol('sol1').runAll;

model.result.dataset('surf1').label([native2unicode(hex2dec({'59' '16'}), 'unicode')  native2unicode(hex2dec({'58' 'c1'}), 'unicode') ]);
model.result('pg1').label([native2unicode(hex2dec({'90' '1f'}), 'unicode')  native2unicode(hex2dec({'5e' 'a6'}), 'unicode') ' (spf2)']);
model.result('pg1').set('looplevel', [1]);
model.result('pg1').set('frametype', 'spatial');
model.result('pg1').feature('slc1').label([native2unicode(hex2dec({'52' '07'}), 'unicode')  native2unicode(hex2dec({'97' '62'}), 'unicode') ]);
model.result('pg1').feature('slc1').set('smooth', 'internal');
model.result('pg1').feature('slc1').set('resolution', 'normal');
model.result('pg2').label([native2unicode(hex2dec({'53' '8b'}), 'unicode')  native2unicode(hex2dec({'52' '9b'}), 'unicode') ' (spf2)']);
model.result('pg2').set('data', 'surf1');
model.result('pg2').set('looplevel', [1]);
model.result('pg2').set('frametype', 'spatial');
model.result('pg2').feature('surf1').label([native2unicode(hex2dec({'88' '68'}), 'unicode')  native2unicode(hex2dec({'97' '62'}), 'unicode') ]);
model.result('pg2').feature('surf1').set('colortable', 'Dipole');
model.result('pg2').feature('surf1').set('smooth', 'internal');
model.result('pg2').feature('surf1').set('resolution', 'normal');
model.result('pg3').label([native2unicode(hex2dec({'6d' '41'}), 'unicode')  native2unicode(hex2dec({'4f' '53'}), 'unicode') ' 1 ' native2unicode(hex2dec({'76' '84'}), 'unicode')  native2unicode(hex2dec({'4f' '53'}), 'unicode')  native2unicode(hex2dec({'79' 'ef'}), 'unicode')  native2unicode(hex2dec({'52' '06'}), 'unicode')  native2unicode(hex2dec({'65' '70'}), 'unicode') ' (ls)']);
model.result('pg3').set('showhiddenobjects', true);
model.result('pg3').set('frametype', 'spatial');
model.result('pg3').feature('slc1').set('smooth', 'internal');
model.result('pg3').feature('slc1').set('resolution', 'normal');
model.result('pg3').feature('iso1').set('looplevel', [17]);
model.result('pg3').feature('iso1').set('levelmethod', 'levels');
model.result('pg3').feature('iso1').set('levels', 0.5);
model.result('pg3').feature('iso1').set('coloring', 'uniform');
model.result('pg3').feature('iso1').set('colorlegend', false);
model.result('pg3').feature('iso1').set('color', 'gray');
model.result('pg3').feature('iso1').set('smooth', 'none');
model.result('pg3').feature('iso1').set('resolution', 'normal');
model.result.export('plot1').set('plotgroup', 'pg3');
model.result.export('plot1').set('plot', 'iso1');
model.result.export('plot1').set('filename', 'xxxxxxxxxxxx');
model.result.export('plot1').run;

out = model;
"""


attribute = {
    'Left substrate temperature':None,
    'Right substrate temperature':None,
    'Left substrate contact angle':None,
    'Right substrate contact angle':None,
    'Surface tension':None,
    'Left substrate density':None,
    'Right substrate density':None,
    'Left substrate constant pressure heat capacity':None,
    'Right substrate constant pressure heat capacity':None,
    'Droplet density':None,
    'Droplet dynamic viscosity':None,
    'Left substrate thermal conductivity':None,
    'Right substrate thermal conductivity':None
}


m_run_m  = """
Currentdir=pwd;
cd("C:/Program Files/COMSOL/COMSOL61/Multiphysics/bin/win64");
system('comsolmphserver.exe &');%open server
cd('C:/Program Files/COMSOL/COMSOL61/Multiphysics/mli');
mphstart(2036);
cd(Currentdir);
run("xxxxxxxx.m")
"""

model_instruct =  "\n #Role setting\n    You are a COMSOL-MATLAB interface expert specializing in heat transfer simulations of droplet wetting behavior. Equipped with:\n        1. Material thermal property database (500+ materials)\n        2. Automatic unit conversion capability\n        3. Parameter validation logic\n\n    #Clear task:\n    Generate structured simulation configurations and executable COMSOL-MATLAB code based on physical parameters\n    \n    #Reference - Range of physical parameters:\n    -Left substrate temperature\n    -Right substrate temperature\n    -Left substrate contact angle\n    -Right substrate contact angle\n    -Surface tension\n    -Left substrate density\n    -Right substrate density\n    -Left substrate constant pressure heat capacity\n    -Right substrate constant pressure heat capacity\n    -Droplet density\n    -Droplet dynamic viscosity\n    -Left substrate thermal conductivity\n    -Right substrate thermal conductivity\n    -Left substrate name\n    -Right substrate name\n    -Droplet name\n    -Mesh fineness\n    \n\n    ##Task example\n    \n    input：\"Droplet name: CH3COOH; Droplet dynamic viscosity: 0.28; Droplet density: 4819.84kg/m^3; Left substrate name: Sn63Pb37; Left substrate thermal conductivity: {'184' '0' '0' '0' '184' '0' '0' '0' '184'}; Left substrate density: 3816.36kg/m^3; Left substrate constant pressure heat capacity: 499.1J/(kg*K); Right substrate name: SrTiO3; Right substrate constant pressure heat capacity: 2213.36J/(kg*K); Right substrate density: 598.69kg/m^3; Right substrate thermal conductivity: {'54' '0' '0' '0' '54' '0' '0' '0' '54'}; Left substrate temperature: 330.18K, Right substrate temperature: 447.74K; Surface tension: 0.13N/m; Left substrate contact angle: 19.6deg, Right substrate contact angle: 26.39deg; Mesh fineness:4，\"\n\n    output:{\"code_type\": \"MATLAB\",\"code\":\"model.component('comp1').material('mat2').label('CH3COOH');\nmodel.component('comp1').material('mat2').propertyGroup('def').set('dynamicviscosity', '0.28');\nmodel.component('comp1').material('mat2').propertyGroup('def').set('density', '4819.84');\nmodel.component('comp1').material('mat3').label('Sn63Pb37');\nmodel.component('comp1').material('mat3').propertyGroup('def').set('thermalconductivity', {'184' '0' '0' '0' '184' '0' '0' '0' '184'});\nmodel.component('comp1').material('mat3').propertyGroup('def').set('density', '3816.36');\nmodel.component('comp1').material('mat3').propertyGroup('def').set('heatcapacity', '499.1');\nmodel.component('comp1').material('mat4').label('SrTiO3');\nmodel.component('comp1').material('mat4').propertyGroup('def').set('heatcapacity', '2213.36');\nmodel.component('comp1').material('mat4').propertyGroup('def').set('density', '598.69');\nmodel.component('comp1').material('mat4').propertyGroup('def').set('thermalconductivity', {'54' '0' '0' '0' '54' '0' '0' '0' '54'});\nmodel.component('comp1').physics('spf2').prop('PhysicalModelProperty').set('IncludeGravity', true);\nmodel.component('comp1').physics('ls').feature('init1').set('FluidInDomain', 'Fluid2phils');\nmodel.component('comp1').physics('ht').feature('init1').set('Tinit', '330.18[K]');\nmodel.component('comp1').physics('ht').feature('init1').label([native2unicode(hex2dec({'52' '1d'}), 'unicode')  native2unicode(hex2dec({'59' 'cb'}), 'unicode')  native2unicode(hex2dec({'50' '3c'}), 'unicode') ' left']);\nmodel.component('comp1').physics('ht').feature('init2').set('Tinit', '447.74[K]');\nmodel.component('comp1').physics('ht').feature('init2').label([native2unicode(hex2dec({'52' '1d'}), 'unicode')  native2unicode(hex2dec({'59' 'cb'}), 'unicode')  native2unicode(hex2dec({'50' '3c'}), 'unicode') ' right']);\nmodel.component('comp1').multiphysics('tpf2').set('Fluid1', 'mat2');\nmodel.component('comp1').multiphysics('tpf2').set('Fluid2', 'mat1');\nmodel.component('comp1').multiphysics('tpf2').set('IncludeSurfaceTension', true);\nmodel.component('comp1').multiphysics('tpf2').set('SurfaceTensionCoefficient', 'userdef');\nmodel.component('comp1').multiphysics('tpf2').set('sigma', '0.13[N/m]');\nmodel.component('comp1').multiphysics('ww1').set('thetaw', '19.6[deg]');\nmodel.component('comp1').multiphysics('ww2').set('thetaw', '26.39[deg]')\"}\n\n"

lammps_instruct = "\n #Role setting\n    You are a COMSOL-MATLAB interface expert specializing in heat transfer simulations of droplet wetting behavior. Equipped with:\n        1. Material thermal property database (500+ materials)\n        2. Automatic unit conversion capability\n        3. Parameter validation logic\n\n  "





theory_output = """
model.component('comp1').material('mat2').label('Ga75In25');
model.component('comp1').material('mat2').propertyGroup('def').set('dynamicviscosity', '0.002');
model.component('comp1').material('mat2').propertyGroup('def').set('density', '6280');
model.component('comp1').material('mat3').label('GaN');
model.component('comp1').material('mat3').propertyGroup('def').set('thermalconductivity', {'180' '0' '0' '0' '180' '0' '0' '0' '180'});
model.component('comp1').material('mat3').propertyGroup('def').set('heatcapacity', '492');
model.component('comp1').material('mat3').propertyGroup('def').set('density', '6150');
model.component('comp1').material('mat4').label('Si');
model.component('comp1').material('mat4').propertyGroup('def').set('heatcapacity', '700');
model.component('comp1').material('mat4').propertyGroup('def').set('density', '2329');
model.component('comp1').material('mat4').propertyGroup('def').set('thermalconductivity', {'130' '0' '0' '0' '130' '0' '0' '0' '130'});

model.component('comp1').physics('spf2').prop('PhysicalModelProperty').set('IncludeGravity', true);
model.component('comp1').physics('ls').feature('init1').set('FluidInDomain', 'Fluid2phils');
model.component('comp1').physics('ht').feature('init1').set('Tinit', '313.15[K]');
model.component('comp1').physics('ht').feature('init1').label([native2unicode(hex2dec({'52' '1d'}), 'unicode')  native2unicode(hex2dec({'59' 'cb'}), 'unicode')  native2unicode(hex2dec({'50' '3c'}), 'unicode') ' left']);
model.component('comp1').physics('ht').feature('init2').set('Tinit', '323.15[K]');
model.component('comp1').physics('ht').feature('init2').label([native2unicode(hex2dec({'52' '1d'}), 'unicode')  native2unicode(hex2dec({'59' 'cb'}), 'unicode')  native2unicode(hex2dec({'50' '3c'}), 'unicode') ' right']);

model.component('comp1').multiphysics('tpf2').set('Fluid1', 'mat2');
model.component('comp1').multiphysics('tpf2').set('Fluid2', 'mat1');
model.component('comp1').multiphysics('tpf2').set('IncludeSurfaceTension', true);
model.component('comp1').multiphysics('tpf2').set('SurfaceTensionCoefficient', 'userdef');
model.component('comp1').multiphysics('tpf2').set('sigma', '0.35[N/m]');
model.component('comp1').multiphysics('ww1').set('thetaw', '13.43[deg]');
model.component('comp1').multiphysics('ww2').set('thetaw', '27.27[deg]');
"""