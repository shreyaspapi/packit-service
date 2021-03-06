from http import HTTPStatus
from logging import getLogger
from flask import make_response
from json import dumps

try:
    from flask_restx import Namespace, Resource
except ModuleNotFoundError:
    from flask_restplus import Namespace, Resource

from packit_service.service.api.parsers import indices, pagination_arguments
from packit_service.models import GitProjectModel

logger = getLogger("packit_service")

ns = Namespace(
    "projects", description="Repositories which have Packit Service enabled."
)


@ns.route("")
class ProjectsList(Resource):
    @ns.expect(pagination_arguments)
    @ns.response(HTTPStatus.PARTIAL_CONTENT, "Projects list follows")
    @ns.response(HTTPStatus.OK, "OK")
    def get(self):
        """List all GitProjects"""

        result = []
        first, last = indices()

        projects_list = GitProjectModel.get_projects(first, last)
        if not projects_list:
            return ([], HTTPStatus.OK)
        for project in projects_list:
            project_info = {
                "namespace": project.namespace,
                "repo_name": project.repo_name,
                "project_url": project.project_url,
                "prs_handled": len(project.pull_requests),
                "branches_handled": len(project.branches),
                "releases_handled": len(project.releases),
                "issues_handled": len(project.issues),
            }
            result.append(project_info)

        resp = make_response(dumps(result), HTTPStatus.PARTIAL_CONTENT)
        resp.headers["Content-Range"] = f"git-projects {first + 1}-{last}/*"
        resp.headers["Content-Type"] = "application/json"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp


@ns.route("/<forge>/<namespace>/<repo_name>/prs")
@ns.param("forge", "Git Forge")
@ns.param("namespace", "Namespace")
@ns.param("repo_name", "Repo Name")
class ProjectsPRs(Resource):
    @ns.expect(pagination_arguments)
    @ns.response(
        HTTPStatus.PARTIAL_CONTENT, "Project PRs handled by Packit Service follow"
    )
    @ns.response(HTTPStatus.OK, "OK")
    def get(self, forge, namespace, repo_name):
        """List PRs"""

        result = []
        first, last = indices()

        pr_list = GitProjectModel.get_project_prs(
            first, last, forge, namespace, repo_name
        )
        if not pr_list:
            return ([], HTTPStatus.OK)
        for pr in pr_list:
            pr_info = {
                "pr_id": pr.pr_id,
                "builds": [],
                "tests": [],
            }
            copr_builds = []
            test_runs = []
            for build in pr.get_copr_builds():
                build_info = {
                    "build_id": build.build_id,
                    "chroot": build.target,
                    "status": build.status,
                    "web_url": build.web_url,
                }
                copr_builds.append(build_info)
            pr_info["builds"] = copr_builds
            for test_run in pr.get_test_runs():
                test_info = {
                    "pipeline_id": test_run.pipeline_id,
                    "chroot": test_run.target,
                    "status": str(test_run.status),
                    "web_url": test_run.web_url,
                }
                test_runs.append(test_info)
            pr_info["tests"] = test_runs

            result.append(pr_info)

        resp = make_response(dumps(result), HTTPStatus.PARTIAL_CONTENT)
        resp.headers["Content-Range"] = f"git-project-prs {first + 1}-{last}/*"
        resp.headers["Content-Type"] = "application/json"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp


@ns.route("/<forge>/<namespace>/<repo_name>/issues")
@ns.param("forge", "Git Forge")
@ns.param("namespace", "Namespace")
@ns.param("repo_name", "Repo Name")
class ProjectIssues(Resource):
    @ns.response(HTTPStatus.OK, "OK, project issues handled by Packit Service follow")
    def get(self, forge, namespace, repo_name):
        """Project issues"""
        issues_list = GitProjectModel.get_project_issues(forge, namespace, repo_name)
        if not issues_list:
            return ([], HTTPStatus.OK)
        result = {"issues": []}
        for issue in issues_list:
            result["issues"].append(issue.issue_id)
        resp = make_response(dumps(result))
        resp.headers["Content-Type"] = "application/json"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp


@ns.route("/<forge>/<namespace>/<repo_name>/releases")
@ns.param("forge", "Git Forge")
@ns.param("namespace", "Namespace")
@ns.param("repo_name", "Repo Name")
class ProjectReleases(Resource):
    @ns.response(HTTPStatus.OK, "OK, project releases handled by Packit Service follow")
    def get(self, forge, namespace, repo_name):
        """Project releases"""
        releases_list = GitProjectModel.get_project_releases(
            forge, namespace, repo_name
        )
        if not releases_list:
            return ([], HTTPStatus.OK)
        result = []
        for release in releases_list:
            release_info = {
                "tag_name": release.tag_name,
                "commit_hash": release.commit_hash,
            }
            result.append(release_info)
        resp = make_response(dumps(result))
        resp.headers["Content-Type"] = "application/json"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
