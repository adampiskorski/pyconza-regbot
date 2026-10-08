{
  description = "pyconza-regbot dev shell with uv and Python 3.14";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixpkgs-python.url = "github:cachix/nixpkgs-python";
  };

  outputs = { self, nixpkgs, nixpkgs-python }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      pythonVersion = "3.14";
      myPython = pkgs.python314;
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          myPython
          pkgs.uv
          pkgs.gcc
          pkgs.pkg-config
          pkgs.openssl
          pkgs.zlib
          pkgs.libffi
          pkgs.nixpkgs-fmt
          pkgs.act
        ];
        shellHook = ''
          export UV_PYTHON=${myPython}/bin/python${pythonVersion}
          export UV_NO_MANAGED_PYTHON=1
          # manylinux wheels need these on NixOS
          export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib pkgs.zlib pkgs.openssl pkgs.libffi ]}''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
        '';
      };
    };
}
