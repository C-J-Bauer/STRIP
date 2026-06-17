#include <gamma.h>
#include <iostream>
#include <string>

using std::cerr;
using std::endl;

std::string output_file_root = "fid_jspectrum";

int main(int argc, char** argv)
{
    char* sys_file = 0;
    if (argc > 1) {
        sys_file = argv[1];
    } else {
        cerr << "usage: " << argv[0] << " <sys_file>" << endl;
        exit(1);
    }

    // DEFINE SYSTEM & NMR PARAMETERS
    const double dt1 = 0.032;       // t1 time increment
    const double dt2 = 0.004;       // t2 time increment
    const int t1Size = 512;         // points on t1 axis
    const int t2Size = 4096;         // points on t2 axis
    spin_system sys;                // define the system, read in
    sys.read(sys_file);          // from disk
    std::string binary_file = output_file_root + ".fid";
    std::ofstream fid(binary_file, std::ios::binary | std::ios::out);

                                    // SET UP NECESSARY VARIABLES
    // block_1D tmp(t2pts);            // 1D-data block storage
    // block_2D data(t1pts, t2pts);    // 2D-data matrix storage
    row_vector oned(t2Size);
    gen_op H = Hcs(sys) + HJ(sys); // Hamiltonian, strong coupling
    gen_op detect = Fm(sys);        // F- for detection operator
    gen_op sigma0, sigma1, sigma, sigma2, sigma3;   // working density matrices
    gen_op sigma_pulse_1, sigma_te_1, sigma_te_180;
    // APPLY PULSE SEQUENCE
    sigma0 = sigma_eq(sys);            // equilibrium density matrix
    sigma1 = Iypuls(sys, sigma0, 90);
    for (int t1 = 0; t1 < t1Size; t1++) {

        sigma2 = evolve(sigma1, H, t1*dt1/2.0);
        sigma3 = Ixpuls(sys, sigma2, 180);
        sigma = evolve(sigma3, H, t1*dt1/2.0);

        FID(sigma, detect, H, dt2, t2Size, oned); // acquisition
        std::vector<double> real = {};
        std::vector<double> imag = {};
        double relaxation = 1.0;
        double decay_t1 = exp(-t1 * dt1/relaxation);
        if (t1 == 0) {
            decay_t1 *= 0.5;
        }
        for (int t2 = 0; t2 < t2Size; t2++) 
        {
            double sample_time = t2 * dt2;
            double decay = exp(-sample_time/relaxation) * decay_t1;
            if (t2 == 0) {
                real.push_back(oned.getRe(t2) * decay * 0.5);
                imag.push_back(oned.getIm(t2) * decay * 0.5); 
            } else {
                real.push_back(oned.getRe(t2) * decay );
                imag.push_back(oned.getIm(t2) * decay); 
            }         
        }
        // save real array to binary file
        fid.write(reinterpret_cast<const char*>(real.data()), real.size() * sizeof(double));
        fid.write(reinterpret_cast<const char*>(imag.data()), imag.size() * sizeof(double));
    }
    fid.close();

    std::string params_file = output_file_root + ".json";
    std::ofstream params(params_file);
    params << "{\"t1Size\": " << t1Size << ", \"t2Size\": " << t2Size << ", \"dt1\": " << dt1 << ", \"dt2\": " << dt2 << "}" << std::endl;
    params.close();
}