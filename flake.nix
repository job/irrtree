{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, ... } @ inputs:
    let
      pname = "irrtree";
      version = "1.4.0";
    in

    inputs.flake-utils.lib.eachDefaultSystem (system:

      let
        pkgs = inputs.nixpkgs.legacyPackages.${system};
        pythonPackages = pkgs.python3.pkgs;
      in

      rec {

        packages = {
          ${pname} = pythonPackages.buildPythonApplication {
            inherit pname version;
            src = ./.;
            propagatedBuildInputs = with pythonPackages; [
              asciitree
              progressbar2
            ];
          };
          default = packages.${pname};
        };

        apps = {
          ${pname} = inputs.flake-utils.lib.mkApp {
            drv = packages.default;
          };
          default = apps.${pname};
        };

      });
}
