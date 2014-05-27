#!/usr/bin/env python

from __future__ import division
import numpy as np
import os.path
from matplotlib.pyplot import *
from matplotlib.colors import LinearSegmentedColormap
from numpy import cos, sin, pi, real, imag, abs, sqrt, exp, angle
from scipy.linalg import eig, eigvals, inv, norm
from scipy.integrate import trapz, ode, complex_ode, odeint


class FileOperations():
    """Simple  class to handle the output of class parameters to stdout and
    a .cfg file.
    
        ### possibly outdated -> json.dumps ###
    """
    
    def __init__(self, filename=None):
        filename = '{}.cfg'.format(filename)
        self.file = open(filename, 'a')
        
    def write(self, text):
        print text
        self.file.write(text)
        self.file.write("\n")
    
    def close(self):
        self.file.close()
        

def c_eig(H, left=False, **kwargs):
    """Wrapper for scipy.linalg.eig(H) that returns modified eigenvalues
    and eigenvectors.
    
    The returned vectors are normalized according to the biorthogonal product, i.e.,
        
        <psi_l|phi_r> = delta_{psi,phi}
    
    with
    
        H|psi_r> = E|psi_r>, <psi_l|H = <psi_l|E ,
    
    instead of the standard (hermitian) inner product
    
        (|psi>.dagger) * |psi> = 1
    
        
        Parameters:
        -----------
            H:  (2,2) ndarray
                Hamiltonian matrix
            left: bool (default: False)
                Whether to calculate left eigenvectors as well
    
        Returns:
        --------
          eigenvalues:  (2,)   ndarray
          left eigenvectors:  (2,2)  ndarray
          right eigenvectors: (2,2)  ndarray
    """
    
    # get eigenvalues and eigenvalues of matrix H
    # multiple possibilities:
    # 1) from option left=True
    eVals, eVecs_l, eVecs_r = eig(H, left=True, **kwargs)
    eVecs_l = eVecs_l.conj()
    #print np.einsum('ij,ij -> i', eVecs_r.conj(), eVecs_r)
    #print np.einsum('ij,ij -> i', eVecs_l.conj(), eVecs_l)
    #test_eigenvalues(eVals, eVecs_l, eVecs_r, H)
    
    # 2) left eigenvalues are the (transposed) right eigenvectors of H.T
    # (results in extremely large eigenvectors)
    #eVals, eVecs_r = eig(H, **kwargs)
    #_, eVecs_l = eig(H.T, **kwargs)
    #test_eigenvalues(eVals, eVecs_l, eVecs_r, H)
    
    # 3) X_L * X_R = 1, X_L = inv(X_R).T
    #eVals, eVecs_r = eig(H, **kwargs)
    #eVecs_l = inv(eVecs_r).T
    #test_eigenvalues(eVals, eVecs_l, eVecs_r, H)
    
    # normalize eigenvectors wrt biorthogonality
    c_norm = lambda ev_l, ev_r: np.sqrt(ev_l.dot(ev_r))
    
    for n in (0, 1):
        # here one has freedom to have N = N_r * N_l, i.e.,
        # rho = rho_r * rho_l and
        # alpha = alpha_r + alpha_l
        N = c_norm(eVecs_l[:,n],eVecs_r[:,n])
        #eVecs_l[:,n] /= N**1
        eVecs_l[:,n] /= N**2
        # leave right eigenvectors normalized via abs(eVecs_r)**2 = 1 
        #eVecs_r[:,n] /= N**1
        
    #print "after R:", np.einsum('ij,ij -> i', eVecs_r.conj(), eVecs_r)
    #print "after L:", np.einsum('ij,ij -> i', eVecs_l.conj(), eVecs_l)
        
    if left is True:                              
        return eVals, eVecs_l, eVecs_r
    else:
        return eVals, eVecs_r


def c_trapz(f, dx, **kwargs):
    """Wrapper for scipy.integrate.trapz that allows to integrate complex-valued
    arrays.
    
        Parameters:
        -----------
            f:  (N,) ndarray
           dx:  float
        Returns:
        --------
            c_trapz: (N,) ndarray
    """
    
    real_int = trapz(real(f), dx=dx, **kwargs)
    imag_int = trapz(imag(f), dx=dx, **kwargs)
    
    return real_int + 1j*imag_int


def c_gradient(f, dx):
    """Wrapper for numpy.gradient that allows to calculate gradients for complex-
    valued arrrays.
    
        Parameters:
        -----------
            f: (N,) ndarray
            dx: float
            
        Returns:
        --------
            c_gradient: (N,) ndarray
    """
    
    real_grad = np.gradient(real(f), dx)
    imag_grad = np.gradient(imag(f), dx)
    
    return real_grad + 1j*imag_grad


def map_trajectory(c1, c2, E1, E2):
    """
    Function to determine the trajectory's character based on
    the amplitude's absolute values a and b.
    
        Parameters:
        -----------
            c1, c2: ndarray
                Absolute values of amplitudes c1 and c2.
            E1, E2: ndarray
                Real or imaginary parts of the energies E1 and E2.
        Returns:
        --------
            mapped trajectory: ndarray
    """
    
    N = np.sqrt(c1**2 + c2**2)
    return (E1*c1 + E2*c2)/N


def set_scientific_axes(ax, axis='x'):
    """Set axes to scientific notation."""
    
    #ax.ticklabel_format(style='sci', axis=axis, scilimits=(0,0), useOffset=False)
    ax.ticklabel_format(style='plain', axis=axis, useOffset=False)
    ax.xaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_locator(MaxNLocator(4))
    #xticks(rotation=30)


def cmap_discretize(cmap, indices):
    """Discretize colormap according to indices list.
    
        Parameters:
        -----------
            cmap: str or Colormap instance
            indices: list
        
        Returns:
        --------
            segmented colormap
    """
    
    if type(cmap) == str:
        cmap = get_cmap(cmap)
        
    indices = np.ma.concatenate([[0],indices,[1]])
    N = len(indices)
    
    colors_i = np.concatenate((np.linspace(0,1.,N),
                               (0.,0.,0.,0.)))
    colors_rgba = cmap(colors_i)
    
    cdict = {}
    for ki, key in enumerate(('red','green','blue')):
        cdict[key] = [ (indices[i], colors_rgba[i-1,ki],
                        colors_rgba[i,ki]) for i in xrange(N) ]
        
    return LinearSegmentedColormap(cmap.name + "_%d"%N, cdict, 1024)


def draw_arrow(loop_direction, init_loop_phase, x0=0., y0=0., R=1.5, phi=pi/8.):
    """Draw arrow with specified pointing direction.
    
        ### outdated ###
    
    """
    
    x1, y1 = x0 + R*cos(-phi+init_loop_phase), y0 + R*sin(-phi+init_loop_phase)
    x2, y2 = x0 + R*cos(phi+init_loop_phase),  y0 + R*sin(phi+init_loop_phase)
    
    if loop_direction == '-':
        arr = '<|-'
    elif loop_direction == '+':
        arr = '-|>'
    else:
        raise Exception("Invalid loop_direction %s!" % loop_direction)
   
    annotate("",
             xy=(x1, y1), xycoords='data',
             xytext=(x2, y2), textcoords='data',
             arrowprops=dict(arrowstyle=arr, lw=1.5, #linestyle="dashed",
                             connectionstyle="arc3,rad=-0.3")
             )


def test_eigenvalues(eVals, eVecs_l, eVecs_r, H):
    """Test eigenvalue problem.
    
    The output contains both the eigenvalues and eigenvectors (left and right),
    as well as the left and right hand sides of the eigenvalue equations
    
        H v_i = E_i v_i
    or
        v_i H = E_i v_i
    
    respectively.
    
        Parameters:
        -----------
            eVals: (2,) ndarray
            eVecs_l: (2,2) ndarray
            eVecs_r: (2,2) ndarray
            H: (2,2) ndarray
        
        Returns:
        --------
            None
    """
    
    print 50*"#"
    print
    print "eVals\n ", eVals
    print "eVecs_r\n", eVecs_r
    print "eVecs_l\n", eVecs_l
    print
    
    for n in (0,1):
        print "ev_l*H\n  ", eVecs_l[:,n].dot(H)
        print "e1*ev_l\n  ", eVals[n]*eVecs_l[:,n]
        print
        print "H*ev_r\n  ", H.dot(eVecs_r[:,n])
        print "e1*ev_r\n  ", eVals[n]*eVecs_r[:,n]
        print
        
    print 50*"#"


if __name__ == '__main__':
    pass

