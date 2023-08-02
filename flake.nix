{
  description = "The Heart of YouCube. See the documentation at https://youcube.madefor.cc.";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-unstable";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, utils, }:
    utils.lib.eachSystem [
      "x86_64-linux"
      "aarch64-linux"
      "x86_64-darwin"
      "aarch64-darwin"
    ]
      (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          version = builtins.substring 0 8 self.lastModifiedDate;
          deps = with pkgs.python3Packages; [
            sanic
            yt-dlp
            ujson
            spotipy
          ];
        in
        {
          packages = {
            default = pkgs.python3Packages.buildPythonApplication {
              pname = "youcube";
              inherit version;
              src = ./.;
              format = "pyproject";
              patchPhase = "rm src/requirements.txt";
              buildInputs = [ pkgs.python3Packages.setuptools ];
              nativeBuildInputs = [ pkgs.makeWrapper ];
              propagatedBuildInputs = deps;
              pythonImportsCheck = [ "youcube" ];
              postInstall = ''
                mkdir -p $out/bin
                makeWrapper ${pkgs.python3}/bin/python3 $out/bin/youcube-server \
                  --add-flags "$out/lib/${pkgs.python3.libPrefix}/site-packages/youcube/__main__.py" \
                  --set PYTHONPATH "${pkgs.python3.pkgs.makePythonPath deps}" \
                  --set PATH "${pkgs.lib.makeBinPath [ pkgs.sanjuuni pkgs.ffmpeg ]}"
              '';
            };

            docker =
              let server = self.packages.${system}.default;
              in pkgs.dockerTools.buildLayeredImage {
                name = server.pname;
                tag = server.version;
                contents = [ server pkgs.sanjuuni pkgs.ffmpeg ] ++ self.packages.${system}.default.propagatedBuildInputs;

                config = {
                  Cmd =
                    let pkg = self.packages.${system}.default;
                    in [ "${pkg}/bin/youcube-server" ];
                  WorkingDir = "/";
                };
              };
          };

          defaultApp = utils.lib.mkApp { drv = self.packages.${system}.default; };

          devShells.default = pkgs.mkShell {
            packages = with pkgs; [ python3 python3Packages.pip sanjuuni ffmpeg ];
          };

        }) // {

      nixosModules.default = { config, lib, pkgs, ... }:
        with lib;
        let
          cfg = config.services.youcube-server;
        in
        {
          options.services.youcube-server = {
            enable = mkOption {
              type = types.bool;
              default = false;
            };
            packages = {
              type = types.submodule;
              description = lib.mdDoc "Packages used by YouCube";
              options = {
                sanjuuni = mkPackageOptionMD pkgs "sanjuuni" { };
                ffmpeg = mkPackageOptionMD pkgs "ffmpeg" { };
              };
            };

            spotify = {
              type = types.submodule;
              description = "Spotify support";
              options = {
                credentialsFile = mkOption {
                  type = types.path;
                  description = lib.mdDoc ''
                    File containing the SPOTIFY_CLIENT_ID and
                    SPOTIFY_CLIENT_SECRET in the format of
                    an EnvironmentFile=, as described by systemd.exec(5).
                  '';
                  example = "/etc/nixos/youcube-spotify-credentials";
                  default = null;
                };
              };
            };

            host = mkOption {
              description = lib.mdDoc "The host of the YouCube server.";
              default = "0.0.0.0";
              type = types.string;
            };

            port = mkOption {
              description = lib.mdDoc "YouCube server port.";
              default = 5000;
              type = types.port;
            };
          };

          config = mkIf cfg.enable {
            systemd.services."youcube.youcube-server" = {
              wantedBy = [ "multi-user.target" ];
              after = [ "network.target" ];
              serviceConfig =
                let
                  pkg = self.packages.${system}.default;
                in
                {
                  Restart = "on-failure";
                  ExecStart = "python3 ${pkg}/${pkgs.python3.sitePackages}/youcube/__main__.py";
                  DynamicUser = "yes";
                  RuntimeDirectory = "youcube.youcube-server";
                  RuntimeDirectoryMode = "0755";
                  StateDirectory = "youcube.youcube-server";
                  StateDirectoryMode = "0700";
                  CacheDirectory = "youcube.youcube-server";
                  CacheDirectoryMode = "0750";
                  EnvironmentFile = [ (cfg.spotify.credentialsFile || "/dev/null") ];
                };
              environment = {
                SANJUUNI_PATH = "${cfg.packages.sanjuuni}/bin/sanjuuni";
                FFMPEG_PATH = "${cfg.packages.ffmpeg}/bin/ffmpeg";
                HOST = "${cfg.host}";
                PORT = "${cfg.port}";
              };
            };
          };
        };
    };
}
