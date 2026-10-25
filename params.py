from dataclasses import dataclass

@dataclass(frozen=True)
class Params:
    name: str
    k: int
    eta1: int
    eta2: int
    du: int
    dv: int
    @property
    def ek_size(self): return 384 * self.k + 32
    @property
    def dk_pke_size(self): return 384 * self.k
    @property
    def dk_size(self): return 768 * self.k + 96
    @property
    def c_size(self): return 32 * (self.du * self.k + self.dv)

ML_KEM_512  = Params("ML-KEM-512",  2, 3, 2, 10, 4)
ML_KEM_768  = Params("ML-KEM-768",  3, 2, 2, 10, 4)
ML_KEM_1024 = Params("ML-KEM-1024", 4, 2, 2, 11, 5)