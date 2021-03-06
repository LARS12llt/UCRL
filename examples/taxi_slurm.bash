#!/bin/bash
# N_cpu=16
# N_mem=50g
N_cpu=8
N_mem=10g
N_hours=200
part=24c

duration=160000000
N_parallel_rep=1
repetitions=5
init_seed=(114364114 679848179 375341576 340061651 311346802 945527102 1028531057 358887046 299813034 472903536 650815502 931560826 391431306 111281634 55536093 484610172 131932607 835579495 82081514 603410165 467299485)
exe_file=../example_taximdp.py 


folder=taxi_${dim}_$(date '+%Y%m%d_%H%M%S')
echo ${folder}
mkdir ${folder}


ALGS=(UCRL SCUCRL)
A_SHORT_NAME=(UCRL-taxi SCUCRL-taxi)

SPAN_C=(2 5 10 15 20 25)

# CREATE CONFIGURATIONS

ALPHAS=" --p_alpha 0.1 --r_alpha 0.8 "

for (( pr=0; pr<${N_parallel_rep}; pr++ ))
do
    off=$((pr*repetitions))
    for (( j=0; j<${#ALGS[@]}; j++ ))
    do
        echo ${pr} ${j} ${ALGS[$j]}
        
        i=1
        
        N_t=${#SPAN_C[@]}
        if [ ${ALGS[$j]} == UCRL ]
        then
            N_t=1
        fi
        
        for (( k=0; k<${N_t}; k++ ))
        do
            
            CC=${SPAN_C[$k]}
            if [ ${ALGS[$j]} == UCRL ]
            then
                CC=inf
            fi
            echo ${pr} ${j} ${ALGS[$j]} ${CC}
        
            out_name="${ALGS[$j]}_${pr}_${CC}_%j.out"
            sname=${ALGS[$j]}_${pr}_${dim}.slurm
            fname=${folder}/${sname}
            
            echo "#!/bin/bash" > ${fname}                                                                                                      
            echo "#SBATCH --nodes=1" >> ${fname}
            echo "#SBATCH --partition=${part}" >> ${fname}
            echo "#SBATCH --ntasks-per-node=1" >> ${fname}
            echo "#SBATCH --cpus-per-task=${N_cpu}" >> ${fname}
            echo "#SBATCH --time=${N_hours}:00:00" >> ${fname}
            echo "#SBATCH --job-name=${A_SHORT_NAME[$j]}_${dim}" >> ${fname}
            echo "#SBATCH --mem=${N_mem}" >> ${fname}
            echo "#SBATCH --output=${out_name}" >> ${fname}
            echo "pwd; hostname; date" >> ${fname}
            echo "" >> ${fname}
            echo "module load anaconda3/4.1.0" >> ${fname}
            echo "export OMP_NUM_THREADS=\$SLURM_CPUS_PER_TASK" >> ${fname}
            echo "export NUMEXPR_NUM_THREADS=\$SLURM_CPUS_PER_TASK" >> ${fname}
            
            #cmdp=" --id c${i}"
            cmdp="--rep_offset ${off} --path ${ALGS[$j]}_toy3d_c${i} --span_constraint ${CC} --regret_steps 2000 "
            
            echo "python ${exe_file} --alg ${ALGS[$j]} ${ALPHAS} -n ${duration} -r ${repetitions} --seed ${init_seed[$pr]} ${cmdp}" >> ${fname}
            i=$((i+1))
            # echo "python ${exe_file} -b --alg ${ALGS[$j]} ${ALPHAS} -d ${dim} -n ${duration} --rmax ${rmax} -r ${repetitions} --seed ${init_seed} --id c${i}" >> ${fname}
            # i=$((i+1))

            cd ${folder}
            sbatch ${sname}
            cd ..
            sleep 1
        done
    done
done
